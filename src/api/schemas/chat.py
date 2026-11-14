from typing import Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    mcp_code: str
    interrupt_id: str

class ChatStreamChunk(BaseModel):
    message: str
    summary: Optional[str]