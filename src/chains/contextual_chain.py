from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage
from utils.logger import getLogger
from chains.summarizer_chain import summary_history_prompt

logger = getLogger(__name__)

TEMPLATE="""
<|im_start|>system
You are a retrieval assistant. 
TASK: Formulate a standalone question based on summary.
RULE: 
- Output ONLY the reformulated question. DO NOT answer it. 
- If [No previous chat summary], proofread the question.
<|im_end|>
<|im_start|>user
SUMMARY:
{summary}

QUERY:
{input}
<|im_end|>
<|im_start|>assistant
REFORMULATED:
""".strip()

CONTEXTUALIZE_Q_TEMPLATE = ChatPromptTemplate.from_template(TEMPLATE)

async def contextualize_prompt(llm, input: str, chat_history: list[BaseMessage]) -> tuple[str,str]:
  """
  Use llm to enhance the context of input prompt based on given chat_history.
  """

  logger.info(f"enhancing the context of user input based on chat history.")

  # summarize the previous chat history
  if chat_history:
    summary = await summary_history_prompt(llm=llm, chat_history=chat_history)
  else:
    summary = "[No previous chat summary]"
  
  # build the context enhancer chain
  contextual_chain = CONTEXTUALIZE_Q_TEMPLATE | llm | StrOutputParser()
  
  payload = {
    "input": input, 
    "summary": summary #"\n\n".join(chat_messages)
  }
  
  logger.info({
    "input": f"{input[:60]}...",
    "summary": f"{summary[:60]}..."
  })
  
  # enhance the user input using the recent chat history
  contextual_q_prompt = await contextual_chain.ainvoke(payload)

  logger.info(f"Original input: {input}")
  logger.info(f"Enhanced input: {contextual_q_prompt}")

  return contextual_q_prompt