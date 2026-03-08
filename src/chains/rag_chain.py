import langchain
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from utils.logger import getLogger
from chains.contextual_chain import contextualize_prompt
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from models.chat import ChatMessage
from utils.chat import history_as_turns, formatted_turns

logger = getLogger(__name__)

TEMPLATE="""
<|im_start|>system
You are a helpful AI assistant. Use the following context to answer the user's question.
<|im_end|>

<|im_start>user
Context: 
{context}

History: 
{chat_history}

Query:
{input}
<|im_end|>

<|im_start|>assistant
Your Answer: 
<|im_end|>
"""

QA_PROMPT = ChatPromptTemplate.from_template(TEMPLATE)

async def invoke_question(llm, question: str, chat_history: list[ChatMessage]) -> str:
  logger.info(f"langchain: {langchain.__version__}")

  history = [m.to_base_message() for m in chat_history]
  
  prompt = await contextualize_prompt(llm=llm,
                                      input=question,
                                      chat_history=history)
  
  chain = QA_PROMPT | llm | StrOutputParser()

  logger.info("including the whole chat history as reference..")
  formatted_chat_history = formatted_turns(history_as_turns(history))

  logger.info(f"Invoking prompt..")
  result = await chain.ainvoke({
    "input": prompt, 
    "context": "", 
    "chat_history": "\n\n".join(formatted_chat_history)
  })

  logger.info(f"Result:\n{result}")
  return (prompt, result)
