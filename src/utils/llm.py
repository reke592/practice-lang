import math
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from utils.logger import getLogger
from langchain_core.messages import AIMessage
from utils.environment import LLAMA_URL, NUM_CTX, API_KEY
from langgraph.checkpoint.memory import InMemorySaver

@dataclass
class Context:
  """Custom runtime context schema."""
  user_id: str

logger = getLogger(__name__)

def init_ollama(model: str = "qwen3.5:4b"):
  logger.info(f"model: {model}")
  return ChatOllama(
    base_url=f"{LLAMA_URL}",
    api_key=API_KEY, # type: ignore
    model=model, 
    temperature=0,
    num_ctx=NUM_CTX,
    # logprobs=True,
    # top_logprobs=5,
    reasoning=False,
    # client_kwargs={
    #   "logprobs": True,
    #   "top_logprobs": 5
    # }
  )

def init_gemini(model: str = 'gemini-3.1-flash-lite-preview'):
  logger.info(f"model: {model}")
  return ChatOpenAI(
    model=model,
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
  )
  # return ChatGoogleGenerativeAI(
  #   model=model,
  #   api_key=API_KEY,
  #   temperature=0,
  #   max_tokens=None,
  #   timeout=None,
  #   max_retries=2
  # )

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

# let the model remember the conversation
# CHECKPOINTER = InMemorySaver()

# llm model
# MODEL = init_model(model="qwen3.5:4b")
