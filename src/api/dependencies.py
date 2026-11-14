import json
from fastapi import Depends

from infrastructure.database.client import DatabaseClient, db_client
from infrastructure.database.repositories.documents_repository import DocumentsRepository
from infrastructure.checkpointer.client import get_checkpointer as _get_checkpointer
from utils.embeddings import embedding_func, compressor

def get_db() -> DatabaseClient:
    return db_client

def get_documents_repo(db: DatabaseClient = Depends(get_db)) -> DocumentsRepository:
    return DocumentsRepository(db)

def get_checkpointer():
    return _get_checkpointer()

def get_embedding_func():
    return embedding_func

def get_compressor():
    return compressor

def get_mcp_config():
    with open ("mcp_config.json", "r") as fp:
        mcp_config:dict[str,dict] = json.load(fp)
    return mcp_config
