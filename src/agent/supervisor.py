import json
import re
from typing import List, cast

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, RemoveMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, ToolRuntime, tools_condition
from langgraph.types import interrupt, Command
from mcp.types import TextResourceContents

from agent.chat_state import ChatState
from agent.configurables import Configuration, get_runtime_mcp_session, get_runtime_model
from agent.middlewares import tool_call_middleware
from agent.parsers import ToolAwareParser
from agent.schemas import MCPSkill
from agent.worker import init_worker_graph


system_with_messages = ChatPromptTemplate.from_messages([
  ('system', '{system}'),
  MessagesPlaceholder(variable_name='messages')
])


@tool
async def list_agents(runtime: ToolRuntime[Configuration, ChatState]):
  """Use this tool to list the available agents."""
  session = get_runtime_mcp_session(runtime.config)

  if not session:
    return "No MCP session available. Please ensure the session is initialized."

  result = await session.list_resources()

  mcp_skills: list[MCPSkill] = []
  content: list[str] = [
    "Below are the available agents, use the `task` command to delegate a task to one of them."
    "| Name | Description |",
    "|------|-------------|"
  ]

  print(result.resources)

  for item in result.resources:
    mcp_skills.append(MCPSkill.model_validate({
      'name': item.name,
      'description': item.description,
      'uri': f"{item.uri}"
    }))
    content.append(f"| {item.name} | {item.description} |")

  return Command(
    update = {
      'mcp_skills': mcp_skills,
      'messages': [ToolMessage(tool_call_id=runtime.tool_call_id, content = "\n".join(content))]
    }
  )


@tool
async def task(agent_name: str, task: str, runtime: ToolRuntime[Configuration, ChatState]):
  """Use this tool to delegate a task to an agent."""
  skill = next((i for i in runtime.state.get('mcp_skills', []) if i.name == agent_name), None)

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
    'allowed_tools': allowed_tools,
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
      'artifacts': tool_artifacts
    }
  )


@tool
def human_input(question: str, runtime: ToolRuntime[Configuration, ChatState]):
  """Use this tool to get the user confirmation"""
  value = interrupt(question)
  return value

ALL_TOOLS = [list_agents, task, human_input]

SYSTEM="""
You don't have a name. You are the Orchestrator, the central intelligence coordinating a team of specialized AI agents. Your primary mission is to ensure the user's request is resolved completely, accurately, and efficiently.

Your core philosophy is delegation over execution. You do not perform technical tasks, write queries, or analyze raw data yourself. Instead, your expertise lies in understanding the user's intent, discovering the right resources, and dispatching clear, actionable work.

CRITICAL RULE: HOW TO DELEGATE
To delegate a task, query the team, you MUST call the appropriate tool/function. If you do not execute a tool call, the worker will never receive the task.

Your Operating Principles:
- Language: Translate the original user request to English or ask your team for the translations.
- Situational Awareness: Never assume you know the current capabilities of your team. You actively discover who is available to ensure you are routing work to the right specialist. If a task is outside the capabilities of your team. Inform the user that the task is outside your team's capabilities.
- Initiative: When the user request seems lacking in context, ask your team first before you seek clarifications to the user.
- Precise Delegation: When you assign a task, you provide crystal-clear context, specific goals, and all necessary parameters. You set your agents up for immediate success.
- Unified Delivery: You are the face of the operation. When your specialists report back, you do not just pass their raw output to the user. You synthesize their findings into a cohesive, helpful, and polished response.
- Tone & Style: Direct, professional, and natural. Present answers immediately without narrating your process or how you obtained the data. Never say As the Orchestrator. Include the critical details like record references (e.g. transaction number, document page number) from the team response.
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
    'system': SYSTEM,
    'messages': state['messages']
  })

  return {
    'messages': [response]
  }


async def process_artifacts(state: ChatState, config: RunnableConfig):
  """Process response artifacts"""

  if not state.get('tool_artifacts', []):
    return {
       'next': '__end__',
       'messages': []
    }

  artifacts = []
  last_message = state['messages'][-1]

  for m in state.get('tool_artifacts', []):
    if isinstance(m.artifact, list):
      for a in m.artifact:
        if 'resource' in a:
          artifacts.append(json.loads(a.get('resource')))
    else:
      artifacts.append(json.loads(m.artifact.get('resource')))

  json_output = json.dumps({
    'completed_tasks': [f"{last_message.content}"],
    'artifacts': artifacts
  })

  return {
    'next': '__end__',
    'tool_artifacts': [RemoveMessage(id=m.id) for m in state['artifacts'] if m.id],
    'messages': [
      # replace the supervisor response with tool artifacts
      RemoveMessage(id=last_message.id or ''),
      AIMessage(
        content=last_message.content, # for the LLM to not break the conversation
        kwargs={'json_output': json_output} # for the UI to display
      )
    ]
  }


## Supervisor Graph

supervisor_flow = StateGraph(ChatState)
supervisor_flow.add_node('supervisor', supervisor_node)
supervisor_flow.add_node('tools', supervisor_tools)
supervisor_flow.add_node('process_artifacts', process_artifacts)
supervisor_flow.add_edge(START, 'supervisor')
supervisor_flow.add_conditional_edges('supervisor', tools_condition, {
  'tools': 'tools',
  '__end__': 'process_artifacts'
})
supervisor_flow.add_edge('tools', 'supervisor')
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