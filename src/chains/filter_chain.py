from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage
from utils.logger import getLogger
from utils.chat import history_as_turns, formatted_turns
logger = getLogger(__name__)

# TEMPLATE="""
# <|im_start|>system
# You are a context filter. Analyze the chat history and the latest user query.
# Select and return max of {turn_count} turns from the history that are 
# most relevant to understanding the latest query.
# <|im_end|>

# <|im_start|>user
# HISTORY:
# {chat_history}

# QUERY:
# {input}
# <|im_end|>

# <|im_start|>assistant
# Final List of Relevant History: 
# """.strip()

TEMPLATE="""
<|im_start|>system
You are a retrieval assistant. 
1. Review the HISTORY turns provided.
2. Identify the {turn_count} most recent turns needed to answer the QUERY.
3. Output ONLY the turn numbers (e.g., 1, 2). 
4. DO NOT repeat the content of the turns.
<|im_end|>

<|im_start|>user
HISTORY:
{chat_history}

QUERY: {input}
<|im_end|>

<|im_start|>assistant
The {turn_count} most relevant turn numbers are: Number
""".strip()

Q_TEMPLATE = ChatPromptTemplate.from_template(TEMPLATE)

async def filter_prompt(llm, input: str, chat_history: list[BaseMessage], turn_count=3, window_size=5) -> str:
  """
  Use llm to segment the chat history into turns to identify the most relevant context for the latest user query.
  """

  logger.info(f"segmenting chat history into turns to identify the most relevant context for the latest user query. window_size: {window_size}")
  turns = history_as_turns(chat_history=chat_history[-window_size:])

  logger.info("reversing the search order of turns to ensure the most recent context has the highest influence.")
  turns = turns[::-1]

  if not turns:
    return "No relevanat history."
  
  # filter chain
  chain = Q_TEMPLATE | llm | StrOutputParser()

  # identify the relevant turn ids
  relevant_turns = await chain.ainvoke({
      "input": input, 
      "chat_history": "\n\n".join(formatted_turns(turns)),
      "turn_count": turn_count
    })

  logger.info(f"found relevant turns: {relevant_turns}")

  # select the turns and return the formatted text as final result
  selected = []

  # self-heal just incase the ai hallucinated the return format
  for i in relevant_turns.replace("Turn", "").split(","):
    selected.append(turns[int(i) - 1])

  result = "\n\n".join(formatted_turns(selected))

  logger.info(f"most relevant turns from history: \n{result}")

  return selected
