import asyncio
import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from infrastructure.cache.client import BaseCacheClient
from api.dependencies import get_checkpointer, get_compressor, get_documents_repo, get_embedding_func, get_mcp_config, get_cache
from api.schemas.chat import ChatRequest, ChatCancelRequest
from api.services.chat import delete_chat_checkpoints, process_chat, sse_docs

from langgraph.checkpoint.base import BaseCheckpointSaver

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

@router.post(
    "",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": f"Use this endpoint to send a chat message to the agent. The response is a live stream of updates of message block *not word-by-word*. You need to refresh the UI widget to display the whole paragraph.\n\n{sse_docs}",
            "examples": [
                """
                "data: {"done": false, "msg": "initializing", "int": "", "ct": "cancellation-token", "art": [] }"
                """.strip(),
                """
                "data: {"done": false, "msg": "thinking or interrupt message", "int": "optional interrupt id for next request Human-in-the-loop.", "ct": "", "art": [] }"
                """.strip(),
                """
                "data: {"done": true, "msg": "the final answer", "int": "", "ct": "","art": [{"resource": "generated artifacts URL"}] }"
                """.strip()
            ],
        }
    }
)
async def chat(
    body: ChatRequest,
    checkpointer: BaseCheckpointSaver[str] = Depends(get_checkpointer),
    compressor = Depends(get_compressor),
    embedding_func = Depends(get_embedding_func),
    documents_repo = Depends(get_documents_repo),
    mcp_config = Depends(get_mcp_config),
    cache: BaseCacheClient = Depends(get_cache),
):
    data = process_chat(
        # TODO: auth session
        user_id=1,
        session_id='dev',
        cancellation_token=f"1.dev.{uuid.uuid4()}",
        cache=cache,
        compressor=compressor,
        embedding_func=embedding_func,
        message=body.message,
        mcp_code='dev', #body.mcp_code,
        documents_repo=documents_repo,
        mcp_config=mcp_config,
        checkpointer=checkpointer,
        interrupt_id=body.interrupt_id
    )
    
    return StreamingResponse(data, media_type="text/event-stream")


@router.delete(
    "",
    description="Use this endpoint to clear the chat history."
)
async def clear(checkpointer: BaseCheckpointSaver[str] = Depends(get_checkpointer)):
    await delete_chat_checkpoints(checkpointer=checkpointer, session_id='dev')
    return "Ok"
