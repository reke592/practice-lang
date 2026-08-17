import json
from typing import Callable, List
import warnings

from langchain.tools import BaseTool
from langchain_core.embeddings import Embeddings
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.sessions import Connection, StreamableHttpConnection
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_core.documents import BaseDocumentCompressor
from langchain_core.runnables import RunnableConfig
from langchain_mcp_adapters.client import MultiServerMCPClient
from langfuse import LangfuseSpan, get_client, propagate_attributes
from langfuse.langchain import CallbackHandler
from langgraph.types import Command
from mcp import StdioServerParameters
from rich.console import Console
from rich.markdown import Markdown

from agent.chat_state import ChatState
from agent.supervisor import init_graph as get_ai
from agent.configurables import ChatModels, Configuration
from api.schemas.chat import ChatStreamChunk
from environment import LLM_PROVIDER_MODEL, MAX_TOOL_RETRY
from infrastructure.llm.client import PROVIDERS

# Suppress the specific pandas UserWarning about DBAPI2 objects
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=".*serializer warning.*",
)


# Initialize Langfuse client
langfuse = get_client()

# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler()
console = Console()

_yield_formatter = Callable[[str, bool, str | None], ChatStreamChunk]


def get_composite_thread_id(session_id: str):
    return f"session:{session_id}"


async def delete_chat_checkpoints(checkpointer: BaseCheckpointSaver[str], session_id: str):
    thread_id = get_composite_thread_id(session_id=session_id)
    await checkpointer.adelete_thread(thread_id=thread_id)


async def _process_request(input: dict, config: RunnableConfig, span: LangfuseSpan, interrupt_id: str | None, yield_formatter: _yield_formatter):
    
    # start sending stream chunks
    async for chunk in get_ai().astream(
        input=ChatState(**input) if not interrupt_id else Command(resume=input),
        config=config,
        stream_mode="updates",
        subgraphs=True,
        version="v2",
    ):
        if chunk['type'] == "updates":
            state_data = chunk['data']
            for node, state in state_data.items():

                # when the supervisor call multiple subagents in parallel
                if isinstance(state, list):
                    yield yield_formatter("Synthesizing results", False, None)
                    continue

                # HITL
                if isinstance(state, tuple):
                    if state[0].__class__.__name__ == 'Interrupt':
                        yield yield_formatter(state[0].value, False, state[0].id)
                    continue

                # ignore state updates if it does not contain a message
                if not state or not state.get('messages'):
                    continue

                latest_message = state['messages'][-1]

                # read the message content
                if getattr(latest_message, 'content', None):
                    console.print(f"[dim]{node}: {latest_message.content}[/dim]")

                    # when the llm generates a tool call request
                    if isinstance(latest_message.content, list):
                        yield yield_formatter("Gathering more information", False, None)
                        continue

                    # when the graph receives a tool call response
                    if hasattr(latest_message, 'tool_call_id') and latest_message.tool_call_id:
                        yield yield_formatter("Processing records", False, None)
                        continue

                    # text content
                    yield yield_formatter(latest_message.content, False, None)

                    # json content, this may includes artifact urls
                    if hasattr(latest_message, 'kwargs') and 'json_output' in latest_message.kwargs:
                        yield yield_formatter(latest_message.kwargs['json_output'], False, None)
                    
                elif getattr(latest_message, 'tool_calls', None):
                    tools = [tc['name'] for tc in latest_message.tool_calls]
                    console.print(f"[dim]tools: {tools}[/dim]")
    

async def process_chat(
  message: str,
  session_id: str,
  embedding_func: Embeddings,
  compressor: BaseDocumentCompressor,
  mcp_config: dict[str, Connection],
  mcp_code: str,
  yield_formatter: Callable[[str, bool, str | None], ChatStreamChunk],
  checkpointer: BaseCheckpointSaver[str],
  provider = LLM_PROVIDER_MODEL,
  interrupt_id: str | None = None
):
    # Tracing configurations
    with langfuse.start_as_current_observation(
        name="process-request",
        input=message,
        metadata={
        'model': provider
        }
    ) as span:
        # TODO: tracing id
        trace_user_id = 'dev'

        # Propagate trace to all child observation
        with propagate_attributes(
            user_id=trace_user_id,
            metadata={
                'tenant_id': 'tenant_id',
                'company_id': 'company_id',
                'user_id': 'user_id'
            }
        ):
            composite_thread_id = get_composite_thread_id(session_id=session_id)
            # mcp_config : dict[str, Connection]= {
            #     "coding": StreamableHttpConnection(
            #         transport='streamable_http',
            #         url= "http://coding/mcp",
            #         headers={
            #             'Authorization': f"Bearer token"
            #         },
            #         timeout=60
            #     ),
            #     "dev": StdioServerParameters(
            #         command="node",
            #         args="mcp/build/src/index.js",
            #         env=None
            #     )
            # }
            mcp_client = MultiServerMCPClient(mcp_config)

            run_input = {
                'images': [],
                'messages': [HumanMessage(content=[{'type': 'text', 'text': message.strip()}])],
            }

            if mcp_code in mcp_config:
                async with mcp_client.session(mcp_code) as session:
                    # load MCP tools for config dependencies
                    mcp_tools = await load_mcp_tools(session) if session else [] 
                    configurable = Configuration(
                        thread_id=composite_thread_id,
                        # MCP and document access
                        mcp_session=session,
                        mcp_client=mcp_client,
                        mcp_tools=mcp_tools,
                        max_tool_retry=MAX_TOOL_RETRY,
                        models=ChatModels(**PROVIDERS[provider]),
                        embedding_func=embedding_func,
                        compressor=compressor
                    )
                    run_config = RunnableConfig(
                        configurable=configurable | {},
                        recursion_limit=40,
                        callbacks=[langfuse_handler]
                    )
                    async for m in _process_request(run_input, run_config, span, interrupt_id, yield_formatter):
                        yield m
            else:
                configurable = Configuration(
                    thread_id=composite_thread_id,
                    # MCP and document access
                    mcp_session=None,
                    mcp_client=mcp_client,
                    mcp_tools=None,
                    max_tool_retry=MAX_TOOL_RETRY,
                    models=ChatModels(**PROVIDERS[provider]),
                    embedding_func=embedding_func,
                    compressor=compressor
                )
                run_config = RunnableConfig(
                    configurable=configurable | {},
                    recursion_limit=40,
                    callbacks=[langfuse_handler]
                )
                async for m in _process_request(run_input, run_config, span, interrupt_id, yield_formatter):
                    yield m