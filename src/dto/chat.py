from datetime import datetime
from models.chat import ChatMessage
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from utils.environment import LLAMA_CHAT_MODEL

class Chat(BaseModel):
  session_id: Optional[UUID] = None
  model: str = LLAMA_CHAT_MODEL
  message: str

class ChatResponse(BaseModel):
  session_id: UUID
  model: str = LLAMA_CHAT_MODEL
  response: str
  timestamp: datetime

class ChatHistory(BaseModel):
  session_id: UUID
  messages: List[ChatMessage] = []
