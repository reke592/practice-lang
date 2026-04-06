from dataclasses import dataclass
from langgraph.graph import add_messages
from typing_extensions import Annotated, TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from utils.llm import init_gemini, init_ollama

CHECKPOINTER = InMemorySaver()
LLM = init_gemini()
# LLM = init_ollama()

def soul():
  """reads the content of sould.md for agent behavior"""
  with open(f"src/research_rag/core/soul.md", "r") as f:
    content = f.read()
  return content


@dataclass
class Context:
  """Custom runtime context schema."""
  user_id: str


class RetrievedDocument(TypedDict):
  page_content: str
  source: str


class State(TypedDict):
  messages: Annotated[list, add_messages]
  documents: list[RetrievedDocument] | None
  citations: list[str] | None
  hypothesis: str | None
