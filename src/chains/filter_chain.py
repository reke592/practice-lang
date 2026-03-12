import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage
from utils.logger import getLogger
from utils.chat import history_as_turns, formatted_turns

logger = getLogger(__name__)

NO_HISTORY_DATA="[No history data]"
NO_HISTORY_DATA_PATTERN=r"(?i)\[No\shistory\sdata\]"

RELEVANCE_TEMPLATE = ChatPromptTemplate.from_template("""
<|im_start|>system
# CRITICAL INTERRUPT
If the user QUERY explicitly asks to "ignore chat history", "start over", or "clear context", you MUST stop immediately and output ONLY: {ignore_history_response}

# STANDARD PROCEDURE
1. Identify exactly {turn_count} turn numbers from the provided HISTORY.
2. Output ONLY the digits (e.g., 1, 2). 
3. DO NOT EXPLAIN. DO NOT REPEAT CONTENT.
<|im_end|>

<|im_start|>user
HISTORY:
{chat_history}

QUERY: {input}
<|im_end|>

<|im_start|>assistant
""".strip())

async def filter_prompt(llm, input: str, chat_history: list[BaseMessage], turn_count=1, window_size=8) -> str:
  """
  Use llm to segment the chat history into turns to identify the most relevant context for the latest user query.

  - turn_count >1 will introduce bias, or hallucination when there too many topics in the chat window
  - window_size 5-10, morethan 10 can result to hallucination for small models
  """

  # pick the most recent turns
  logger.info(f"segmenting chat history into turns to identify the most relevant context for the latest user query. window_size: {window_size}")
  turns = history_as_turns(chat_history=chat_history)
  turns = turns[-window_size:]
  turns = formatted_turns(turns[::-1])

  if not turns:
    return NO_HISTORY_DATA
  
  # filter chain
  relevance_chain = RELEVANCE_TEMPLATE | llm | StrOutputParser()

  logger.info("removing duplicate turns by distinction")

  # identify the relevant turn ids
  relevant_turns = await relevance_chain.ainvoke({
      "input": input, 
      "chat_history": "\n\n".join(turns),
      "turn_count": turn_count,
      "ignore_history_response": NO_HISTORY_DATA
    })

  logger.info(f"found relevant turn(s): {relevant_turns}")

  # select the turns and return the formatted text as final result
  selected = []

  if isinstance(relevant_turns, str) and re.match(NO_HISTORY_DATA_PATTERN, relevant_turns):
    return NO_HISTORY_DATA
  
  # self-heal just incase the ai hallucinated the return format
  try:
    for i in relevant_turns.replace("Turn", "").split(","):
      logger.info(turns[int(i) - 1])
      selected.append(turns[int(i) - 1])
    result = "\n".join(selected)
    logger.info(f"most relevant xturns from history: \n{result}")
    return result
  except Exception as e:
    logger.error(e)
    logger.info(f"most relevant turns from history: \n{relevant_turns}")
    return relevant_turns
