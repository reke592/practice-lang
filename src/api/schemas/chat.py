from typing import Optional
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(description="The string message", examples=["Hi"])
    mcp_code: str = Field(description="The MCP Code to use", examples=["dev"])
    interrupt_id: str = Field(description="Interrupt ID from previous conversation, default to empty string.")

class ChatStreamChunk(BaseModel):
    message: str
    summary: Optional[str]