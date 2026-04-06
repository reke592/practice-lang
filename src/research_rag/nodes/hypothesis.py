from langchain.messages import HumanMessage, SystemMessage, AIMessage
# from local_first_RAG.tools import TOOLS
from utils.logger import getLogger
from ..state import LLM, State, soul

_logger = getLogger(__name__)

SYS_PROMPT="""
Given a user's question, write a short, factual paragraph that might appear as an answer. 
Do not say "I think" or "Based on." Just provide the direct hypothetical text. 
Keep it under 100 words.
""".strip()

async def hypothesis(state: State):
  """
  Hypothetical Document Embedding
  """
  _logger.info("processing")

  soul_content = soul()

  question = state["messages"][-1]

  # for hypothesis and web search
  messages = [
    SystemMessage(content=soul_content),
    SystemMessage(content=SYS_PROMPT),
    HumanMessage(content=question.content)
  ]

  # llm_with_tool = LLM.bind_tools(TOOLS)
  response = await LLM.ainvoke(messages)
  _logger.info(f"hypothesis: {response}")
  return { 
    # "messages": [question], 
    "hypothesis": response.content 
  }
