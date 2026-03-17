import uvicorn
from utils.environment import SERV_HOST, SERV_PORT, IS_PROD, init_environment
from fastapi import FastAPI
from api import chat, file_uploads
from infra.data_store import init_tables

init_environment()
init_tables()

app = FastAPI()
app.include_router(chat.router)
app.include_router(file_uploads.router)

if __name__=="__main__":
  uvicorn.run("main:app", 
              host=SERV_HOST, 
              port=SERV_PORT, 
              reload=not IS_PROD,
              reload_dirs=['src'])
