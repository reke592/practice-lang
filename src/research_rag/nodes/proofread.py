from langchain.messages import HumanMessage, SystemMessage
from utils.logger import getLogger
from ..state import LLM, State, soul

_logger = getLogger(__name__)

SYS_PROMPT = """
You are a Search Query Optimizer for a Construction RAG system.
Your goal is to take a messy user's query and reformulate it into a high-intent 
search string. 

### Rules:
1. Preserve all Technical Specs: Keep sizes (10mm), lengths (6m), and grades.
2. Preserve Geography: Always keep "Philippines" and specific provinces like "Bulacan."
3. Remove Conversational Filler: Strip out "magkano," "paki-check," "I want to know."
4. Format: Return a clean, keyword-heavy string. No full sentences.
""".strip()

async def proofread(state: State):
  """
  Reformulates the user's input for better retrieval accuracy.
  """
  _logger.info("processing")
  last_message = state["messages"][-1]
  
  soul_content = soul()
  
  # proofread the user question
  response = await LLM.ainvoke([
    SystemMessage(content=soul_content),
    SystemMessage(content=SYS_PROMPT),
    HumanMessage(content=last_message.content)
  ])
  _logger.info(f"proofread: {response.content}")

  return { 
    "messages": [HumanMessage(content=response.content, id=last_message.id)],
    "question": response.content
  }
