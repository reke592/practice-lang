import math
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from utils.logger import getLogger
from langchain_core.messages import AIMessage

logger = getLogger(__name__)

def init_model(model: str):
  logger.info(f"model: {model}")
  return ChatOpenAI(
    base_url="http://host.docker.internal:11434/v1",
    api_key="ollama", # type: ignore
    model=model, 
    temperature=0,
    # num_ctx=4096,
    logprobs=True,
    top_logprobs=5,
    # model_kwargs={
    #   "num_ctx":4096
    # }
  )


def compute_confidence(response: AIMessage) -> AIMessage:
  response_metadata = response.response_metadata if response else None
  logprobs = response_metadata['logprobs'] if response_metadata else None
  token_logprobs = logprobs['content'] if logprobs else None

  if not token_logprobs:
    logger.info(f"logprobs not available, skipping check.")
    return response
  
  if response_metadata:
    # print(token_logprobs)
    avg_logprobs = sum([lp["logprob"] for lp in token_logprobs]) / len(token_logprobs)
    confidence = math.exp(avg_logprobs) * 100
    logger.info(f"confidence: {confidence}")
    response_metadata['confidence'] = confidence
  
  return response
