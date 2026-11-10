from pathlib import Path

from infrastructure.database.repositories.documents_repository import DocumentsRepository

async def save_embeddings(file_path: str, repo: DocumentsRepository, user_id: int, title: str):
  """
  Load a file and save its embeddings to the database
  """
  clean_path = Path(file_path.strip().replace("..\\", "/").replace("../", "")).resolve().as_posix()

  if not Path(clean_path).exists():
    raise FileNotFoundError(f"File not found: {clean_path}")
    
  return await repo.save_document(user_id=user_id, title=title, file_path=clean_path)
