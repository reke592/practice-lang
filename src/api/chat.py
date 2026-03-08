from datetime import datetime, timezone
from uuid import uuid4, UUID
from dto.chat import Chat, ChatResponse, ChatHistory
from models.chat import ChatSession, ChatMessage
from fastapi import APIRouter
from chains.rag_chain import invoke_question
from infra.data_store import get_cursor, check_session_id, create_session, save_messages, get_chat_history
from utils.logger import getLogger

logger = getLogger(__name__)

router = APIRouter(
  prefix="/chat",
  tags=["chat"]
)

@router.post("/")
async def post_chat(chat: Chat) -> ChatResponse:
  session_id=None
  response=None
  chat_history=[]

  with get_cursor() as cursor:
    logger.info("TODO: fetch the chat history to enhance the prompt and document retrieval")
    session_id = chat.session_id if check_session_id(chat.session_id, cursor) else create_session(chat.message, cursor) 
    chat_history = get_chat_history(session_id, cursor)

  logger.info(f"resolved session_id: {session_id}")

  response = await invoke_question(
    model=chat.model, 
    question=chat.message,
    chat_history=chat_history)
  
  messages = [
    {"role": "human", "content": chat.message },
    {"role": "ai", "content": response}
  ]
  
  with get_cursor() as cursor:
    save_messages(session_id=session_id,
                  messages=messages,
                  cursor=cursor)

  return ChatResponse(
    model=chat.model,
    session_id=session_id,
    response=response,
    timestamp=datetime.now(timezone.utc))


@router.get("/sessions")
async def get_sessions() -> list[ChatSession]:
  return []


@router.get("/messages")
async def get_messages(session_id: UUID) -> ChatHistory:
  chat_history = []
  with get_cursor() as cursor:
    chat_history = get_chat_history(session_id, cursor)

  return ChatHistory(
    session_id=session_id,
    topic="",
    messages=chat_history
  )
