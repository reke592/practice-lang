from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from uuid import UUID

class ChatSession(BaseModel):
  session_id: UUID
  topic: str

class ChatMessage(BaseModel):
  role: str
  content: str
  timestamp: str

  def __str__(self):
    return f"{self.role.upper()} : {self.content}"
  
  def to_base_message(self):
    if self.role == "human" or self.role == "user":
      return HumanMessage(content=self.content)
    elif self.role == "ai" or self.role == "assistant":
      return AIMessage(content=self.content)
    elif self.role == "system":
      return SystemMessage(content=self.content)
    raise TypeError(f"Unsupported type: {self.role}")
