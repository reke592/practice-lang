from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage
from utils.logger import getLogger
from chains.filter_chain import filter_prompt

logger = getLogger(__name__)

# TEMPLATE="""
# <system>
# Given a chat history and the latest user question 
# which might reference context in the chat history, 
# formulate a standalone question which can be undertood 
# without the chat history. Do NOT answer the question, 
# just reformulate it if needed and otherwise return it as is.
# </system>

# <history>
# {chat_history}
# </history>

# <current_user_query>
# {input}
# </current_user_query>

# Final Standalone Question: 
# """.strip()
TEMPLATE="""
<|im_start|>system
Given a chat history and the latest user question 
which might reference context in the chat history, 
formulate a standalone question which can be undertood 
without the chat history. Do NOT answer the question, 
just reformulate it if needed and otherwise return it as is.
<|im_end|>

<|im_start|>user
HISTORY:
{chat_history}

QUERY:
{input}
<|im_end|>

<|im_start|>assistant
Final Standalone Question: 
""".strip()

CONTEXTUALIZE_Q_TEMPLATE = ChatPromptTemplate.from_template(TEMPLATE)

async def contextualize_prompt(llm, input: str, chat_history: list[BaseMessage], turn_count=3, window_size=8) -> str:
  """
  Use llm to enhance the context of input prompt based on given chat_history.
  """

  logger.info(f"enhancing the context of user input based on chat history. window_size: {window_size}, turn_count: {turn_count}")

  # identify relevant history
  relevant_history = await filter_prompt(llm=llm,
                                         input=input,
                                         chat_history=chat_history,
                                         turn_count=turn_count,
                                         window_size=window_size)

  
  # build the context enhancer chain
  contextual_chain = CONTEXTUALIZE_Q_TEMPLATE | llm | StrOutputParser()

  # enhance the user input using the recent chat history
  contextual_q_prompt = await contextual_chain.ainvoke({
      "input": input, 
      "chat_history": relevant_history #"\n\n".join(chat_messages)
    })

  logger.info(f"Original input: {input}")
  logger.info(f"Enhanced input: {contextual_q_prompt}")

  return contextual_q_prompt
