from fastapi import Depends

from infrastructure.database.client import DatabaseClient, db_client
from infrastructure.database.repositories.documents_repository import DocumentsRepository

def get_db() -> DatabaseClient:
    """
    Dependency function to get the database client.
    """
    return db_client

def get_documents_repo(db: DatabaseClient = Depends(get_db)) -> DocumentsRepository:
    """
    Dependency function to get the DocumentsRepository.
    """
    return DocumentsRepository(db)