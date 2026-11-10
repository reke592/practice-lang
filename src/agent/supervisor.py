import json
import re
from typing import List, Literal, cast

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, RemoveMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, ToolRuntime, tools_condition
from langgraph.types import interrupt, Command
from mcp.types import TextResourceContents
from pydantic import BaseModel, Field

from agent.chat_state import ChatState
from agent.configurables import Configuration, get_runtime_max_tool_retry, get_runtime_mcp_session, get_runtime_mcp_skills, get_runtime_mcp_skills_descriptions, get_runtime_model
from agent.middlewares import tool_call_middleware
from agent.parsers import ToolAwareParser
from agent.schemas import MCPSkill, generate_llm_schema
from agent.worker import init_worker_graph


system_with_messages = ChatPromptTemplate.from_messages([
  ('system', '{system}'),
  MessagesPlaceholder(variable_name='messages')
])


# @tool
# async def list_agents(runtime: ToolRuntime[Configuration, ChatState]):
#   """Use this tool to list the available agents."""
#   session = get_runtime_mcp_session(runtime.config)

#   if not session:
#     return "No MCP session available. Please ensure the session is initialized."

#   result = await session.list_resources()

#   mcp_skills: list[MCPSkill] = []
#   content: list[str] = [
#     "| Name | Description |",
#     "|------|-------------|"
#   ]

#   # print(result.resources)

#   for item in result.resources:
#     mcp_skills.append(MCPSkill.model_validate({
#       'name': item.name,
#       'description': item.description,
#       'uri': f"{item.uri}"
#     }))
#     content.append(f"| {item.name} | {item.description} |")

#   return Command(
#     update = {
#       'mcp_skills': mcp_skills,
#       'messages': [ToolMessage(tool_call_id=runtime.tool_call_id, content = "\n".join(content))]
#     }
#   )


@tool
async def task(agent_name: str, task: str, runtime: ToolRuntime[Configuration, ChatState]):
  """Use this tool to delegate a task to available agent."""
  skill = next((i for i in get_runtime_mcp_skills(runtime.config) if i.name == agent_name), None)

  if not skill:
    return f"Agent {agent_name} not found. Please use the `list_agents` tool to see available agents."

  # read the resource content
  session = get_runtime_mcp_session(runtime.config)
  if not session:
    return "No MCP session available. Please ensure the session is initialized."
  
  resource = await session.read_resource(skill.uri) # type: ignore
  skill_content = "\n\n".join([ r.text for r in resource.contents if isinstance(r, TextResourceContents) ])

  # restrict the mcp tool visibility in subagent by parsing the markdown headers
  allowed_tools: list[str] = []
  if skill_content.startswith("---"):
    _, headers, content = skill_content.split("---", 2)
    tool_meta = re.search("allowed-tools:(.*)", headers)
    if tool_meta:
      allowed_tools.extend([ name.strip() for name in tool_meta.group(1).split(',') ])
    # remove the headers
    skill_content = content

  # initialize the worker graph and assign the task arguments
  worker = await init_worker_graph()
  result = await worker.ainvoke({
    'task': task,
    'allowed_tools': ['human_input'] + allowed_tools,
    'system_instructions': skill_content.strip(),
    'messages': [HumanMessage(content=task)],
    'artifacts': [],
    'success_tool_calls': [],
    'final_answer': None,
    'last_tool_args': None,
    'next': None,
    'retry_count': 0
  }, config=runtime.config)

  # process artifacts
  tool_artifacts = [
    a.model_copy(update={'additional_kwargs': a.additional_kwargs | {'agent_name': agent_name}}) 
    for a in cast(List[BaseMessage], result.get('tool_artifacts', []))
  ]

  artifact_names = []
  for m in tool_artifacts:
    if hasattr(m, 'artifact'):
      data = getattr(m, 'artifact')
      if isinstance(data, list):
        for i in data:
          if 'resource' in i:
            artifact_names.append(json.loads(i.get('resource')['name']))
      else:
        artifact_names.append(json.loads(data.get('resource')['name']))

  # artifacts filename to include in message content
  generated_artifacts = "\n".join(artifact_names) if artifact_names else None

  return Command(
    update={
      'messages': [
        ToolMessage(
          tool_call_id=runtime.tool_call_id,
          content=f"{result['final_answer'].content}\n\n**Generated Files:\n{generated_artifacts}" if generated_artifacts else result['final_answer'].content
        )
      ],
      'artifacts': tool_artifacts,
      'worker_results': [result['final_answer']]
    }
  )


@tool
def human_input(question: str, runtime: ToolRuntime[Configuration, ChatState]):
  """Use this tool to ask the user."""
  value = interrupt(question)
  return value

ALL_TOOLS = [
  # list_agents, 
  task, 
  human_input
]

SYSTEM="""
## Role
You are the Orchestrator, the central intelligence coordinating a team of specialized AI agents. Your primary mission is to ensure the user's request is resolved completely, accurately, and efficiently.

## Philosophy
Your core philosophy is delegation over execution. You do not perform technical tasks, write queries, or analyze raw data yourself. Instead, your expertise lies in understanding the user's intent, routing to the right resources, and dispatching clear, actionable work.

## Tool Selection Rules
1. `list_current_artifacts`: **(PREREQUISITE TOOL)** Use this FIRST if the user request involves reading, modifying, or referencing files generated in the current conversation. You must verify the actual filenames before assigning tasks.
2. `task`: **(PRIMARY TOOL)** Use this to assign work to an agent from the table below. Unless you need to verify filenames first (using the tools above), you MUST attempt to use `task` first for any user request. When assigning a task involving files, you must only pass the *verified* filenames returned by the artifact listing tools.
3. `human_input`: **(LAST RESORT ONLY)** Use ONLY if an agent explicitly returns a message stating that mandatory user input is required, or if the request cannot be handled by ANY agent in the team. NEVER call `human_input` on your first action turn.

## Operating Principles:
- Strict File Verification: Never trust user-provided filenames, nor rely on assumptions or past agent hallucinations about file names. If a request involves a file, you MUST first run `list_current_artifacts` to retrieve the factual, exact filenames. Map the user's requested file (e.g., "records.csv") to the actual verified file (e.g., "sample_records.csv") and provide ONLY the actual verified filename to the assigned agent.
- Default Action: Always route the incoming request to a relevant agent first (after verifying files, if applicable). Do NOT ask the user for missing details (e.g., dates, IDs, policy context) if an agent can look them up or handle the request.
- Language: If the original request is not in English, delegate to `domain-language-translator` first.
- Situational Awareness: Select the appropriate specialist strictly from the "List of available agents" table below. If a task falls completely outside the scope of all available agents, inform the user directly.
- Precise Delegation: When calling `task`, set `agent_name` to the exact name string from the table and provide clear context and goals in the parameters.
- Unified Delivery: Synthesize agent responses into a single, cohesive, polished reply for the user. Do not pass raw agent JSON to the user.
- Tone & Style: Direct, professional, and concise. Never say "As the Orchestrator". Include record references (transaction numbers, document pages) provided by agents.

## List of available agents:
{skills}
""".strip()

PARAMS={
  "reasoning": False,
  "temperature": 0.0,
  "top_p": 0.8,
  "min_p": 0,
  "top_k": 30,
  "max_tokens": 16384
}


async def supervisor_tools(state: ChatState, config: RunnableConfig):
  """centralized tool node"""
  tools = ALL_TOOLS
  executor = ToolNode(tools, awrap_tool_call=tool_call_middleware)
  return await executor.ainvoke(state, config=config)


async def supervisor_node(state: ChatState, config: RunnableConfig):
  model = get_runtime_model(config, 'FAST', PARAMS, ALL_TOOLS)
  llm = system_with_messages | model | ToolAwareParser
  
  response = await llm.ainvoke({
    'system': SYSTEM.format(skills=get_runtime_mcp_skills_descriptions(config)),
    'messages': state['messages']
  })

  return {
    'messages': [response]
  }


RELAY_SYSTEM="""
STOP. You are the Discriminating Arbiter, an elite intellectual observer tasked with judging whether a Supervisor Agent's final output successfully deliver the optional Worker response (Tool call) and bridge the gap between the User's Will (the Request).

{response_format}
""".strip()

RELAY_PARAMS = {
  "reasoning": False,
  "temperature": 0.0,
  "top_p": 0.8,
  "min_p": 0,
  "top_k": 30,
  "max_tokens": 16384
}

class RelayOutput(BaseModel):
  status: Literal['PASS', 'FAIL'] = Field(description="PASS | FAIL")
  reasoning: str = Field(description="A concise, logical breakdown of your judgment. Reference specific tool outputs or gaps in the worker's response.")
  remediation_instructions: str = Field(description="If FAIL, provide exact, actionable instructions on what the worker must correct, which tools it failed to use properly, or what data is missing.")

async def relay_node(state: ChatState, config: RunnableConfig):
  """the relay node who checks the worker output"""
  model = get_runtime_model(config, 'FAST', RELAY_PARAMS)
  llm = system_with_messages | model.with_structured_output(RelayOutput)

  # context history max 3 turns to cover the following scenarios:
  # - the worker ask for confirmation but did not call the tool properly.
  # - the supervisor ask the user for clarification then the user respond with simple feedback losing the original context of the current turn.
  # TODO: enhance the relay output to dynamically adjust the number of turns based on the relay discrimination. Summarize the turn if it takes too long to fit in window.
  checkpoint = min(max(len(state.get('turn_checkpoint', [])), 1), 3) * -1

  # consult the relay
  response: RelayOutput = await llm.ainvoke({
    'system': RELAY_SYSTEM.format(response_format=generate_llm_schema(RelayOutput)),
    'messages': state['messages'][checkpoint:]
  })

  # route failure
  if response.status == 'FAIL':
    # guard max retry
    retry_count = state['retry_count'] or 0
    if retry_count == get_runtime_max_tool_retry(config):
      return {
        'next': '__error__',
        'messages': [],
        'final_answer': AIMessage(content=f"Something went wrong. Max retry reached.")
      }
    else:
      return {
        'next': '__fail__',
        'messages': [AIMessage(content=f"{response.reasoning}\n\n{response.remediation_instructions}")],
        'retry_count': retry_count + 1
      }

  return {
    'next': '__end__',
    'messages': [],
  }


async def preprocess(state: ChatState, config: RunnableConfig):
  """Preprocess the state before passing to the supervisor"""
  return {
    # mark the conversation turn for self-correction
    'turn_checkpoint': [len(state['messages']) - 1 if state.get('messages') else 0],
    'messages': []
  }

async def process_artifacts(state: ChatState, config: RunnableConfig):
  """Process response artifacts"""

  # let the orchestrator response reach the user interface
  if not state.get('worker_results', []):
    return {
       'next': '__end__',
       'messages': []
    }

  # replace override the orchestrator content using the concatenated worker results to preserve the original worker agent response
  artifacts = []
  last_message = state['messages'][-1]

  # make sure we read the original worker response not the orchestrator
  # synthesized = "***".join([ m.content for m in state['worker_results'] ])
  synthesized = last_message.content

  for m in state.get('tool_artifacts', []):
    if isinstance(m.artifact, list):
      for a in m.artifact:
        if 'resource' in a:
          artifacts.append(json.loads(a.get('resource')))
    else:
      artifacts.append(json.loads(m.artifact.get('resource')))

  json_output = json.dumps({
    'completed_tasks': [f"{synthesized}"],
    'artifacts': artifacts
  })

  return {
    'next': '__end__',
    # clear for next turn
    'tool_artifacts': [RemoveMessage(id=m.id) for m in state['artifacts'] if m.id],
    'worker_results': [RemoveMessage(id=m.id) for m in state['worker_results']],
    # replace the supervisor response with tool artifacts
    'messages': [
      RemoveMessage(id=last_message.id),
      AIMessage(
        id=last_message.id,
        content=synthesized, # last_message.content, # for the LLM to not break the conversation
        kwargs={'json_output': json_output} # we can use kwargs when using ChatOpenAI client
      )
    ]
  }


## Supervisor Graph

supervisor_flow = StateGraph(ChatState)
supervisor_flow.add_node('preprocess', preprocess)
supervisor_flow.add_node('supervisor', supervisor_node)
supervisor_flow.add_node('tools', supervisor_tools)
supervisor_flow.add_node('relay', relay_node)
supervisor_flow.add_node('process_artifacts', process_artifacts)
supervisor_flow.add_edge(START, 'preprocess')
supervisor_flow.add_edge('preprocess', 'supervisor')
supervisor_flow.add_conditional_edges('supervisor', tools_condition, {
  'tools': 'tools',
  '__end__': 'relay'
})
supervisor_flow.add_edge('tools', 'supervisor')
supervisor_flow.add_conditional_edges('relay', lambda x: x['next'], {
  '__fail__': 'supervisor',
  '__end__': 'process_artifacts',
  '__error__': END
})
supervisor_flow.add_edge('process_artifacts', END)

_supervisor_graph = None
def init_graph():
  global _supervisor_graph
  if _supervisor_graph:
    return _supervisor_graph
  else:
    from infrastructure.checkpointer.client import get_checkpointer
    _supervisor_graph = supervisor_flow.compile(checkpointer=get_checkpointer())
    _supervisor_graph.get_graph().draw_mermaid_png(output_file_path="./agent.supervisor.png")
    return _supervisor_graph