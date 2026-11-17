from fastapi import APIRouter, Depends

from api.dependencies import get_cache
from api.schemas.chat import ChatCancelRequest
from infrastructure.cache.client import BaseCacheClient

router = APIRouter(
    prefix="/cancel",
    tags=["cancel"]
)

@router.post(
    "",
    description="Cancel the running process."
)
async def cancel_running_request(body: ChatCancelRequest, cache: BaseCacheClient = Depends(get_cache)):
    await cache.set_cancellation(body.cancellation_token)
    return "Ok"