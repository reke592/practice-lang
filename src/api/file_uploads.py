from fastapi import APIRouter, UploadFile, File
from utils.logger import getLogger
from uuid import uuid4, UUID
from pathlib import Path
from pydantic import WithJsonSchema
from typing import List, Annotated
from models.chat import ChatFile
import infra.vector_store as vector_store
import infra.data_store as data_store
import shutil
import os

logger = getLogger(__name__)

UPLOADS_DIR=Path("var/session_files")
UPLOADS_DIR.mkdir(exist_ok=True)

router = APIRouter(
  tags=["chat"]
)

# This tells Swagger UI to render a file picker instead of a text box
FilesParam = List[Annotated[
    UploadFile, 
    WithJsonSchema({"type": "string", "format": "binary"})
]]


def count_folders(path: str):
  # List all items and check if each is a directory
  folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
  return len(folders)


@router.post("/session/{id}/files")
async def upload_chat_files(id:UUID, files: FilesParam=File(...)):
  result:List[ChatFile] = []
  session_id = str(id)
  for file in files:
    dest = UPLOADS_DIR / session_id / file.filename
    Path(os.path.dirname(dest)).mkdir(exist_ok=True)
    if os.path.exists(dest):
      os.unlink(dest)
    with dest.open("wb") as buffer:
      shutil.copyfileobj(file.file, buffer)
    
    with data_store.get_cursor() as cursor:
      record=data_store.save_chat_file(session_id=session_id, 
                                       source=file.filename, 
                                       cursor=cursor)
      vector_store.save_document(session_id=id,
                                 abspath=str(dest),
                                 file_id=record.file_id)
      result.append(record)
  return result


@router.get("/sessions/{id}/files")
async def get_chat_files(id: UUID) -> list:
  files: List[ChatFile] = []
  with data_store.get_cursor() as cursor:
    files = data_store.get_chat_files(session_id=id, 
                                      cursor=cursor)
  return files


@router.delete("/sessions/{session_id}/files/{file_id}")
async def delete_chat_file(session_id: UUID, file_id: int):
  with data_store.get_cursor() as cursor:
    data_store.delete_chat_file(session_id=session_id, 
                                file_id=file_id, 
                                cursor=cursor)
    vector_store.delete_document(session_id=session_id,
                                 file_id=file_id)
                                