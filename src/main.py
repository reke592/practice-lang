from fastapi import FastAPI
from api import chat
from infra.data_store import init_tables

init_tables()

app = FastAPI()
app.include_router(chat.router)
