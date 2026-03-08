from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils.logger import getLogger

logger = getLogger(__name__)

TEMPLATE="""
<|im_start|>system
You are a professional editor. 
TASK: Generate a concise title about the context of the Q&A.
CONSTRAINT: Do not exceed {num_words} words. No punctuation at the end.
<|im_end|>

<|im_start|>user
QUESTION:
{question}

ANSWER:
{answer}
<|im_end|>

<|im_start|>assistant
Title: 
<|im_end|>
""".strip()

QA_PROMPT=ChatPromptTemplate.from_template(TEMPLATE)

async def title_generator_prompt(llm, question: str, answer: str, num_words: int = 5) -> str:
  """
  Use llm to generate a session title
  """

  contextual_chain = QA_PROMPT | llm | StrOutputParser()

  result = await contextual_chain.ainvoke({
    "question": question, 
    "answer": answer, 
    "num_words": num_words
  })

  logger.info(f"generated title for the new session: {result}")

  return result
