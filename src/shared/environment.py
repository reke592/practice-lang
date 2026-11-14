import os
from dotenv import load_dotenv
from pydantic import SecretStr
from pathlib import Path

load_dotenv()

def setup_directory(path: str) -> Path:
  target = Path(path)
  target.mkdir(parents=True, exist_ok=True)
  return target

IS_PRODUCTION = os.getenv("IS_PRODUCTION", "false").lower() == "true"

# directories
DATA_DIR = setup_directory(os.getenv("DATA_DIR", "var/"))
TEMP_DIR = setup_directory(os.getenv("TEMP_DIR", "tmp/"))
UPLOADS_DIR = setup_directory(os.getenv("UPLOADS_DIR", "uploads/"))

# build info
BUILD_COMMIT_ID = os.getenv("BUILD_COMMIT_ID", "local")

# LLM client settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
LLM_PROVIDER_API_KEY = SecretStr(os.getenv("LLM_PROVIDER_API_KEY", "ollama-key"))
LLM_PROVIDER_MODEL = os.getenv("LLM_PROVIDER_MODEL", "gemma4:e2b")
LLM_PROVIDER_BASE_URL = os.getenv("LLM_PROVIDER_BASE_URL", "http://host.docker.internal:11434")
LLM_DEFAULT_TEMPERATURE = float(os.getenv("LLM_DEFAULT_TEMPERATURE", 0))  # deterministic
LLM_DEFAULT_MAX_TOKENS = int(os.getenv("LLM_DEFAULT_MAX_TOKENS", 2048))

# Embedding settings
EMBED_PROVIDER = os.getenv("EMBED_PROVIDER", "ollama")
EMBED_PROVIDER_API_KEY = SecretStr(os.getenv("EMBED_PROVIDER_API_KEY", "ollama-key"))
EMBED_PROVIDER_BASE_URL = os.getenv("EMBED_PROVIDER_BASE_URL", "http://host.docker.internal:11434")
EMBED_PROVIDER_MODEL = os.getenv("EMBED_PROVIDER_MODEL", "nomic-embed-text-v2-moe")
RANKER_MODEL = os.getenv("RANKER_MODEL", "ms-marco-MiniLM-L-12-v2")

# PostgreSQL configuration (main database)
DB_HOST=os.getenv("DB_HOST", "postgres")
DB_PORT=int(os.getenv("DB_PORT", '5432'))
DB_NAME=os.getenv("DB_NAME", "practice_lang")
DB_USER=os.getenv("DB_USER", "dev")
DB_PASSWORD=SecretStr(os.getenv("DB_PASSWORD", "dev"))

# Checkpointer database configuration, default to main database if not set
CHECKPOINTER_CLIENT=os.getenv("CHECKPOINTER_CLIENT", "memory")  # options: memory, postgre
CHECKPOINTER_DB_HOST=os.getenv("CHECKPOINTER_DB_HOST", DB_HOST)
CHECKPOINTER_DB_PORT=int(os.getenv("CHECKPOINTER_DB_PORT", str(DB_PORT)))
CHECKPOINTER_DB_NAME=os.getenv("CHECKPOINTER_DB_NAME", DB_NAME)
CHECKPOINTER_DB_USER=os.getenv("CHECKPOINTER_DB_USER", DB_USER)
CHECKPOINTER_DB_PASSWORD=SecretStr(os.getenv("CHECKPOINTER_DB_PASSWORD", DB_PASSWORD.get_secret_value()))

# API static
JWT_SECRET_KEY_FILE=os.getenv("JWT_SECRET_KEY_FILE", DATA_DIR / "jwt.secret")
JWT_ALGORITHM=os.getenv("JWT_ALGORITHM", "HS256")

# Agent harness
MAX_TOOL_RETRY=int(os.getenv("MAX_TOOL_RETRY", '3'))

# Tracing
LANGFUSE_SECRET_KEY=SecretStr(os.getenv("LANGFUSE_SECRET_KEY", ""))
LANGFUSE_PUBLIC_KEY=os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_BASE_URL=os.getenv("LANGFUSE_BASE_URL", "")