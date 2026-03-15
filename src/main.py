import os
os.environ["ONNXRUNTIME_EXECUTION_PROVIDERS"] = "CPUExecutionProvider"

from fastapi import FastAPI
from api import chat, file_uploads
from infra.data_store import init_tables

init_tables()

app = FastAPI()
app.include_router(chat.router)
app.include_router(file_uploads.router)
