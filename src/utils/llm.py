from langchain_ollama import ChatOllama
from utils.logger import getLogger

logger = getLogger(__name__)

def init_model(model: str):
  logger.info(f"model: {model}")
  return ChatOllama(
    base_url="http://host.docker.internal:11434",
    model=model, 
    temperature=0,
    num_ctx=4096
  )

