from datetime import datetime, timezone
from uuid import uuid4, UUID
from dto.chat import Chat, ChatResponse, ChatHistory
from models.chat import ChatSession, ChatMessage
from fastapi import APIRouter, UploadFile
from chains.rag_chain import invoke_question
from chains.title_generator_chain import title_generator_prompt
from infra.data_store import delete_chat_session, get_chat_sessions, get_cursor, check_session_id, create_session, save_messages, get_chat_history
from utils.logger import getLogger
from utils.llm import init_model

logger = getLogger(__name__)

router = APIRouter(
  tags=["chat"]
)

@router.post("/chat")
async def chat_message(chat: Chat) -> ChatResponse:
  session_id = None
  response = None
  title = None
  chat_history = []
  is_new_session = False
  with get_cursor() as cursor:
    logger.info("TODO: fetch the chat history to enhance the prompt and document retrieval")
    if check_session_id(chat.session_id, cursor):
      session_id = chat.session_id
      chat_history = get_chat_history(session_id=session_id,
                                      cursor=cursor)
    else:
      is_new_session = True
      chat_history = []
  logger.info(f"resolved session_id: {session_id}")
  llm = init_model(model=chat.model)
  prompt, response = await invoke_question(llm=llm,
                                           session_id=session_id,
                                           question=chat.message,
                                           chat_history=chat_history)
  messages = [
    {"role": "human", "content": chat.message },
    {"role": "ai", "content": response}
  ]
  # title for new session
  if is_new_session:
    title = await title_generator_prompt(llm=llm,
                                         question=prompt,
                                         answer=response)
  # update the session history
  with get_cursor() as cursor:
    if is_new_session:
      session_id = create_session(title, cursor)
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
  sessions = []
  with get_cursor() as cursor:
    sessions = get_chat_sessions(cursor)
  return sessions


@router.delete("/sessions/{id}")
async def delete_sessison(id: UUID):
  with get_cursor() as cursor:
    delete_chat_session(id, cursor=cursor)
  return True


@router.get("/sessions/{id}")
async def get_messages(id: UUID) -> ChatHistory:
  chat_history = []
  with get_cursor() as cursor:
    chat_history = get_chat_history(id, cursor)
  return ChatHistory(
    session_id=id,
    messages=chat_history
  )
