from datetime import datetime
from models.chat import ChatMessage
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

class Chat(BaseModel):
  session_id: Optional[UUID] = None
  model: str = "qwen2.5-coder:3b"
  message: str

class ChatResponse(BaseModel):
  session_id: UUID
  model: str = "qwen2.5-coder:3b"
  response: str
  timestamp: datetime

class ChatHistory(BaseModel):
  session_id: UUID
  messages: List[ChatMessage] = []
