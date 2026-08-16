from typing import Optional

from pydantic import BaseModel


class ChatStreamChunk(BaseModel):
    message: str
    summary: Optional[str]