from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from utils.logger import getLogger

logger = getLogger(__name__)

CONTEXTUALIZE_Q_TEMPLATE = ChatPromptTemplate.from_messages([
  ("system", "You are a helpful AI assistant tasked with summarizing chat history."),
  ("human", "PREVIOUS CONVERSATION HISTORY TO SUMMARIZE:"),
  MessagesPlaceholder("chat_history"),
  ("human", "TASK: Summarize the whole conversation above in under {num_words} words which I can use to continue the conversation with different LLM models. Do not add any introductory or concluding remarks. Just the summary.")
])

async def summary_history_prompt(llm, chat_history: list[BaseMessage], num_words: int = 100) -> str:
  """
  Use llm to enhance the context of question prompt based on given chat_history.

  - llm - the model to use
  - chat_history - retrieved from database
  - num_words - the eagerness of the ai to describe the summary.

  sample history:
  [("human", "message"), ("ai", "message")]
  """

  contextual_chain = CONTEXTUALIZE_Q_TEMPLATE | llm | StrOutputParser()

  logger.info(f"History: {len(chat_history)}")
  summary = await contextual_chain.ainvoke({"chat_history": chat_history, "num_words": num_words})

  logger.info(f"Summary: {summary}")

  return summary
