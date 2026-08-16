from typing import List, Literal, TypedDict, cast

from langchain.tools import BaseTool
from langchain_core.documents import BaseDocumentCompressor
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langchain_mcp_adapters.client import MultiServerMCPClient
from mcp import ClientSession

from environment import MAX_TOOL_RETRY


class ChatModels(TypedDict):
  """
  runnable settings injection
  """
  FAST: BaseChatModel
  """low latency used for simple classification"""
  BALANCED: BaseChatModel
  """standard model for agent thinking"""
  PRECISE: BaseChatModel
  """for complex reasoning"""


class Configuration(TypedDict):
  """A dictionary that holds runtime context information for a Runnable."""
  thread_id: str
  mcp_client: MultiServerMCPClient | None
  mcp_session: ClientSession | None
  mcp_tools: List[BaseTool] | None
  max_tool_retry: int
  models: ChatModels
  embedding_func: Embeddings
  compressor: BaseDocumentCompressor


def get_runtime_mcp_client(runnable: RunnableConfig) -> MultiServerMCPClient | None:
  configurable = runnable.get('configurable', {})
  return configurable.get('mcp_client', None)

def get_runtime_mcp_session(runnable: RunnableConfig) -> ClientSession | None:
  configurable = runnable.get('configurable', {})
  return configurable.get('mcp_session', None)

def get_runtime_mcp_tools(runnable: RunnableConfig) -> List[BaseTool]:
  configurable = runnable.get('configurable', {})
  return configurable.get('mcp_tools', [])

def get_runtime_max_tool_retry(runnable: RunnableConfig) -> int:
  configurable = runnable.get('configurable', {})
  return configurable.get('max_tool_retry', MAX_TOOL_RETRY)

def get_runtime_model(runnable: RunnableConfig, speed: Literal['FAST', 'BALANCED', 'PRECISE'], params: dict | None = None, tools: List[BaseTool] | None = None) -> BaseChatModel:
  configurable = runnable.get('configurable', {})
  options = cast(ChatModels, configurable.get('models'))
  model = options[speed]

  if (params):
    model = cast(BaseChatModel, model.bind(**params))

  if (tools):
    model = cast(BaseChatModel, model.bind_tools(tools))

  return model
  