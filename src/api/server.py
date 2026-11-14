import contextlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.environment import BUILD_COMMIT_ID
from infrastructure.database.client import db_client
from infrastructure.checkpointer.client import checkpointer_setup, checkpointer_close

from api.handlers.errors import AppError, app_error_handler, unhandled_error_handler
from api.endpoints.chat import router as chat_router

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
  await db_client.connect()
  await checkpointer_setup()
  yield
  await db_client.disconnect()
  await checkpointer_close()

app = FastAPI(
  title="Practice-Lang",
  description="Practice project LLM Agent",
  version=f"0.0.1 ({BUILD_COMMIT_ID})",
  lifespan=lifespan
)

origins = ['*']
app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=['GET','POST','PUT','PATCH','DELETE'],
  allow_headers=['*']
)

app.include_router(chat_router)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)
