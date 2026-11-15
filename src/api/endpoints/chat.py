from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from api.dependencies import get_checkpointer, get_compressor, get_documents_repo, get_embedding_func, get_mcp_config
from api.schemas.chat import ChatRequest
from api.services.chat import delete_chat_checkpoints, process_chat

from langgraph.checkpoint.base import BaseCheckpointSaver

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

@router.post(
    "/completions",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "live stream of updates. The response message is not word-by-word, You need to refresh the UI widget to display the whole paragraph.",
            "examples": [
                """
                "data: {"is_summary": false, "message": "thinking or interrupt message", "interrupt_id": "optional string to include in next reply when the agent interrupts for HTIL.", "artifacts": [] }"
                """.strip(),
                """
                "data: {"is_summary": true, "message": "the final answer", "interrupt_id": "", "artifacts": [{"resource": "generated artifacts URL"}] }"
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
    mcp_config = Depends(get_mcp_config)
):

    content = process_chat(
        # TODO: auth session
        user_id=1,
        session_id='dev',

        compressor=compressor,
        embedding_func=embedding_func,
        message=body.message,
        mcp_code=body.mcp_code,
        documents_repo=documents_repo,
        mcp_config=mcp_config,
        checkpointer=checkpointer,
        interrupt_id=body.interrupt_id
    )
    
    return StreamingResponse(content, media_type="text/event-stream")


@router.get("/clear")
async def clear(checkpointer: BaseCheckpointSaver[str] = Depends(get_checkpointer)):
    await delete_chat_checkpoints(checkpointer=checkpointer, session_id='dev')
    return "Ok"
