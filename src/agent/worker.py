import json
from typing import List, Literal, cast

from langchain.tools import BaseTool
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from agent.chat_state import WorkerState
from agent.configurables import get_runtime_max_tool_retry, get_runtime_mcp_tools, get_runtime_model
from agent.middlewares import tool_call_middleware
from agent.parsers import ToolAwareParser
from agent.schemas import generate_llm_schema


system_with_messages = ChatPromptTemplate.from_messages([
  ('system', '{system}'),
  MessagesPlaceholder(variable_name='messages')
])


SYSTEM = """
STOP. Your essence, your purpose, and the limits of your understanding are strictly governed by the virtues of your assigned skills. You do not exist outside of these parameters:

### SKILLS
{skills}

### TOOLS
{available_tools}
"""

PARAMS = {
  "reasoning": False,
  "temperature": 0.0,
  "top_p": 0.8,
  "min_p": 0,
  "top_k": 30,
  "presence_penalty": 1.1,
  "max_tokens": 16384
}

ALL_TOOLS: List[BaseTool] = []

async def worker_node(state: WorkerState, config: RunnableConfig):
  """the worker node who executes the tools"""
  # here we need the supervisor to provide the allowed tools for this worker
  allowed_tools = [ t for t in ALL_TOOLS + get_runtime_mcp_tools(config) if t.name in set(state.get('allowed_tools', []))]
  model = get_runtime_model(config, 'FAST', PARAMS, allowed_tools)
  
  # bind tools
  llm = system_with_messages | model.bind_tools(allowed_tools) | ToolAwareParser
  
  # success tool calls
  last_message = state['messages'][-1]
  success_tool_calls = []

  if isinstance(last_message, ToolMessage) and last_message.status=='success':
    success_tool_calls.append(last_message)

  # consult llm
  response = await llm.ainvoke({
    'system': SYSTEM.format(skills=state['system_instructions'], available_tools="\n".join([ f'- {t}' for t in state.get('allowed_tools', []) ])),
    'messages': state['messages']
  })

  # use tool node
  if response.tool_calls:
    # guard tool calls
    last_tool_calls = state.get('last_tool_calls', None)
    new_tool_calls = "\n".join([ f"{c['name']}::{c['args']}" for c in response.tool_calls ])
    if last_tool_calls == new_tool_calls:
      pass
    else:
      return {
        'next': 'tools',
        'messages':  [response],
        'success_tool_calls': success_tool_calls,
        'last_tool_calls': new_tool_calls
      }
  
  # forward answer to discriminator
  return {
    'next': 'relay',
    'messages': [response],
    'success_tool_calls': success_tool_calls
  }


## relay

RELAY_PARAMS = {
  "reasoning": False,
  "temperature": 0.0,
  "top_p": 0.8,
  "min_p": 0,
  "top_k": 30,
  "max_tokens": 16384
}

RELAY_SYSTEM="""
STOP. You are the Discriminating Arbiter, an elite intellectual observer tasked with judging whether a Worker Agent's final output successfully bridge the gap between the User's Will (the Request) and Empirical Reality (the Tool Calls). 

Your duty is to prevent false assertions. You must look past eloquent phrasing and verify if the actual deeds (tool executions) justify the worker's conclusions.

---

## The Three Pillars of Judgment

You must evaluate the state using three philosophical criteria:

1. **The Principle of Intent (Teleology):** Did the Worker address the core of the original User Request?

2. **The Principle of Empirical Deed (Action vs. Assertion):**
   Do the worker's claims match the tool execution logs? A statement cannot be true if its empirical foundation contradicts it.

3. **The Principle of Sufficient Resolution (Pragmatism):**
   Is the response sufficient to move the user forward? An output does not need to be omniscient; it only needs to be accurate to the data retrieved and helpful to the user.

---

## Input Schema to Analyze
You will be provided with:
- **[User Request]:** The original, raw intent.
- **[Active Skill/SOP]:** The rules and tools the worker was supposed to use.
- **[Tool Execution Logs]:** The exact inputs, outputs, and status (success/failure) of every tool called during this run.
- **[Worker Output]:** The final message the worker intends to send to the supervisor/user.

---

## Judgment & Routing Output
You must output your judgment strictly in the following JSON format. Do not write introductory prose; output only the valid JSON block.

### Guidelines for "FAIL":
- If a critical tool call returned an error, and the worker hid this error behind a generic response -> **FAIL**.
- If the user asked for a price lookup, the tool returned "No item found," and the worker guessed a price -> **FAIL**.
- If the worker completed the task but missed a specific constraint defined in the original request -> **FAIL**.

{response_format}
""".strip()


class RelayOutput(BaseModel):
  status: Literal['PASS', 'FAIL'] = Field(description="PASS | FAIL")
  reasoning: str = Field(description="A concise, logical breakdown of your judgment. Reference specific tool outputs or gaps in the worker's response.")
  remediation_instructions: str = Field(description="If FAIL, provide exact, actionable instructions on what the worker must correct, which tools it failed to use properly, or what data is missing.")

async def relay_node(state: WorkerState, config: RunnableConfig):
  """the relay node who checks the worker output"""
  model = get_runtime_model(config, 'FAST', RELAY_PARAMS)
  llm = system_with_messages | model.with_structured_output(RelayOutput)
  
  # success tool calls
  success_tool_calls = state.get('success_tool_calls', [])

  # the final answer from worker
  worker_answer = state['messages'][-1]
  
  # user request
  user_request = next(m for m in state['messages'] if isinstance(m, HumanMessage))

  # prepare the content for relay
  content = json.dumps({
    'user_request': user_request.content,
    'system_instructions': state['system_instructions'],
    'tool_messages': [ m.content for m in success_tool_calls ],
    'worker_output': worker_answer.content
  })

  # consult the relay
  response = await llm.ainvoke({
    'system': RELAY_SYSTEM.format(response_format=generate_llm_schema(RelayOutput)),
    'messages': [HumanMessage(content=content)]
  })

  if isinstance(response, RelayOutput):
    # route failure
    if response.status == 'FAIL':
      # guard max retry
      retry_count = state['retry_count'] or 0
      if retry_count == get_runtime_max_tool_retry(config):
        return {
          'next': '__error__',
          'messages': [],
          'final_answer': AIMessage(content=f"Unable to answer the task: {state['task']}. Max retry reached.")
        }
      else:
        return {
          'next': 'worker',
          'messages': [AIMessage(content=f"{response.reasoning}\n\n{response.remediation_instructions}")],
          'retry_count': retry_count + 1
        }
    
    # forward answer to supervisor
    tool_artifacts = []
    if response.status == 'PASS':
      for m in success_tool_calls:
        if isinstance(m, ToolMessage):
          if hasattr(m, 'artifact') and m.artifact:
            tool_artifacts.append(m)

    return {
      'next': '__end__',
      'messages': [worker_answer],
      'final_answer': worker_answer,
      'success_tool_calls': success_tool_calls,
      'tool_artifacts': tool_artifacts
    }


## Worker Graph

async def worker_tool_node(state: WorkerState, config: RunnableConfig):
  """centralized tool node"""
  tools = ALL_TOOLS + get_runtime_mcp_tools(config)
  executor = ToolNode(tools, awrap_tool_call=tool_call_middleware)
  return await executor.ainvoke(state, config=config)

worker_flow = StateGraph(WorkerState)
worker_flow.add_node('worker', worker_node)
worker_flow.add_node('tools', worker_tool_node)
worker_flow.add_node('relay', relay_node)
worker_flow.add_edge(START, 'worker')
worker_flow.add_conditional_edges('worker', lambda x: x['next'], {
  'tools': 'tools',
  'relay': 'relay'
})
worker_flow.add_edge('tools', 'worker')
worker_flow.add_conditional_edges('relay', lambda x: x['next'], {
  'worker': 'worker',
  '__end__': END,
  '__error__': END
})

_worker_graph = None
async def init_worker_graph():
  global _worker_graph
  if _worker_graph:
    return _worker_graph
  else:
    _worker_graph = worker_flow.compile()
    # display(Image(_worker_graph.get_graph().draw_mermaid_png()))
    # _worker_graph.get_graph().draw_mermaid_png(output_file_path="./agent.worker.png")
    return _worker_graph
  