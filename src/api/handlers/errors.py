from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from shared.logger import getLogger
from shared.errors import AppError, CancellationError

_logger = getLogger(__name__)


class ErrorResponseFormat(BaseModel):
  code: str
  message: str


async def app_error_handler(request: Request, e: AppError):
  status_code = 400

  if isinstance(e, CancellationError):
    status_code = 499
    _logger.info(e.message)

  return JSONResponse(
    status_code=status_code,
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
