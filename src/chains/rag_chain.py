import langchain
from langchain_core.output_parsers import StrOutputParser
from utils.logger import getLogger
from chains.contextual_chain import contextualize_prompt
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from models.chat import ChatMessage
from utils.llm import compute_confidence
from infra.vector_store import retrieve_documents, retrieve_relevant_documents
from uuid import UUID

logger = getLogger(__name__)

TEMPLATE="""
<|im_start|>system
You are a helpful AI assistant. Use the following context to answer the user's question.
<|im_end|>

<|im_start>user
### CONTEXT
{context}

### USER QUESTION
{input}
<|im_end|>

<|im_start|>assistant
Your Answer: 
<|im_end|>
"""

QA_PROMPT = ChatPromptTemplate.from_template(TEMPLATE)

async def invoke_question(llm, session_id: UUID, question: str, chat_history: list[ChatMessage]) -> tuple[str, str]:
  logger.info(f"langchain: {langchain.__version__}")

  logger.info("include chat history as reference..")
  history = [m.to_base_message() for m in chat_history]
  
  prompt = await contextualize_prompt(llm=llm,
                                      input=question,
                                      chat_history=history)
  
  chain = QA_PROMPT | llm | compute_confidence

  logger.info("retrieving documents")
  context = retrieve_relevant_documents(session_id=session_id, query=prompt) if session_id else []
  # for doc in context:
  #   logger.info(f"source: {doc.metadata['source']}")

  payload = {
    "input": prompt, 
    "context": "\n\n".join([doc.page_content for doc in context]) if context else "[No context data]"
  }

  response = await chain.ainvoke(payload)
  result = StrOutputParser().invoke(response)
  color_start='\033[32m'
  color_end='\033[0m'
  logger.info(f"Result:\n{color_start}{result}{color_end}")
  return (prompt, result)
