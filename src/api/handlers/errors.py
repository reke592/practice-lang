from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from shared.logger import getLogger

_logger = getLogger(__name__)


class AppError(Exception):
  def __init__(self, message: str, code: str = "AppError"):
    self.message = message
    self.code = code


class ErrorResponseFormat(BaseModel):
  code: str
  message: str


async def app_error_handler(request: Request, e: AppError):
  return JSONResponse(
    status_code=400,
    content=ErrorResponseFormat.model_validate({
      'code': e.code,
      'message': e.message
    }).model_dump()
  )


async def unhandled_error_handler(request: Request, e: Exception):
  # log internally
  _logger.error(e)
  # hide in public
  return JSONResponse(
    status_code=500,
    content=ErrorResponseFormat.model_validate({
      'code': 'Internal',
      'message': 'Internal Server Error'
    }).model_dump()
  )
