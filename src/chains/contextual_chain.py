from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage
from utils.logger import getLogger
from utils.llm import compute_confidence
from utils.chat import history_as_turns, formatted_turns
from chains.summarizer_chain import summary_history_prompt
import re

logger = getLogger(__name__)

TEMPLATE="""
<|im_start|>system
You are a grammarian and conversation editor.
### CRITICAL RULE: 
- Output ONLY the reformulated question. DO NOT answer it. 
- If [No previous chat summary], proofread the question.
- If the latest question is unrelated to the summary or recent messages, only proofread it without adding context.
- If the query is already clear and self-contained, return it unchanged.
- Do NOT correct the spelling of technical terms, names or IDs.
### TASK: Formulate a standalone question using the latest user query which can be understood based on the given summary and recent messages.
<|im_end|>
<|im_start|>user
### SUMMARY:
{summary}

## RECENT MESSAGES:
{history}

## QUERY:
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
  
  # recent messages
  turns = formatted_turns(history_as_turns(chat_history=chat_history))[-5:]

  history = "\n\n".join(turns)

  # build the context enhancer chain
  contextual_chain = CONTEXTUALIZE_Q_TEMPLATE | llm | compute_confidence

  payload = {
    "input": input, 
    "summary": summary,
    "history": history
  }
  
  logger.info({
    "input": f"{input[:60]}...",
    "summary": f"{summary[:60]}..."
  })
  
  # enhance the user input using the recent chat history
  response = await contextual_chain.ainvoke(payload)
  contextual_q_prompt = StrOutputParser().invoke(response)

  logger.info(f"Original input: {input}")
  logger.info(f"Enhanced input: {contextual_q_prompt}")

  return contextual_q_prompt
