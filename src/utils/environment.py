import os
from dotenv import load_dotenv

load_dotenv()

def init_environment():
  os.environ["ONNXRUNTIME_EXECUTION_PROVIDERS"] = "CPUExecutionProvider"

ENV = os.environ.get("ENV", "dev").lower()
IS_PROD = True if not ENV == "dev" else False
DATA_DIR = os.environ.get("UPLOADS_DIR", "var").lower()
TEMP_DIR = os.environ.get("TEMP_DIR", "tmp").lower()
SERV_PORT = int(os.environ.get("SERV_PORT", "8000"))
SERV_HOST = os.environ.get("SERV_HOST", "localhost")
LLAMA_URL = os.environ.get("LLAMA_URL", "http://localhost:11434")
LLAMA_CHAT_MODEL = os.environ.get("LLAMA_CHAT_MODEL", "qwen3.5:4b")
LLAMA_EMBED_MODEL = os.environ.get("LLAMA_EMBED_MODEL", "nomic-embed-text")
RANKER_MODEL = os.environ.get("RANKER_MODEL", "ms-marco-MiniLM-L-12-v2")
