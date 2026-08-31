from typing import Annotated, List, TypedDict

from langchain.messages import ToolMessage
from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import add_messages

from agent.schemas import MCPSkill

class WorkerState(TypedDict):
  """The state of a subagent worker"""
  next: str | None
  task: str
  system_instructions: str
  allowed_tools: List[str]
  success_tool_calls: Annotated[List[ToolMessage], add_messages]
  messages: Annotated[List[BaseMessage], add_messages]
  retry_count: int | None
  last_tool_args: str | None
  """we use this to prevent the tool call loop"""
  final_answer: AIMessage | None
  artifacts: Annotated[List[BaseMessage], add_messages] 

class ChatState(TypedDict):
  """The state of the user-facing chatbot"""
  messages: Annotated[List[BaseMessage], add_messages]
  artifacts: Annotated[List[BaseMessage], add_messages]
  mcp_skills: List[MCPSkill] | None
  worker_results: Annotated[List[BaseMessage], add_messages]
