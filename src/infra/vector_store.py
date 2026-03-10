import os
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from uuid import UUID
from utils.logger import getLogger

logger=getLogger(__name__)

embedding_func = OllamaEmbeddings(model="nomic-embed-text", base_url="http://host.docker.internal:11434")

VS_CHAT_FILES="chat_files"

# Initialize stores
_chat_files = Chroma(
  collection_name=VS_CHAT_FILES, # Keep a consistent name
  embedding_function=embedding_func,
  persist_directory="var/chroma"
)


text_splitter = RecursiveCharacterTextSplitter(
  chunk_size=1000,
  chunk_overlap=200,
  length_function=len
)


def read_path_to_docs(folder_path: str) -> list[tuple[Document, str]]:
  logger.info(f"read_path_to_docs: {folder_path}")
  documents = []
  for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)
    if filename.endswith(".pdf"):
      loader = PyPDFLoader(file_path)
    elif filename.endswith(".docx"):
      loader = Docx2txtLoader(file_path)
    else:
      raise TypeError("Unsupported file type")
    documents.extend((loader.load(), filename))
  return documents


# TODO: connect to RAG and perform similarity sesarch
def read_path_to_doc(abspath: str) -> tuple[Document, str]:
  logger.info(f"read_path_to_doc: {abspath}")
  if abspath.endswith(".pdf"):
    loader = PyPDFLoader(abspath)
  elif abspath.endswith(".docx"):
    loader = Docx2txtLoader(abspath)
  else:
    raise TypeError(f"Unsupported file type: {os.path.basename(abspath)}")
  return (loader.load(), os.path.basename(abspath))


def save_document(session_id: UUID, abspath: str, file_id:int,):
  logger.info(f"save_document, session: {session_id}, file_id: {file_id}")
  doc, filename = read_path_to_doc(abspath=abspath)
  chunks = text_splitter.split_documents(doc)
  session_str=str(session_id)
  file_id_str=str(file_id)
  # delete current embeddings
  _chat_files.delete(where={
    "$and": [
      {"session_id": session_str},
      {"file_id": file_id_str}
    ]
  })
  # connect embedding to session using metadata
  for chunk in chunks:
    chunk.metadata['session_id'] = session_str
    chunk.metadata['file_id'] = file_id_str
  # save
  _chat_files.add_documents(documents=chunks)


def delete_document(session_id: UUID, file_id:int):
  logger.info("delete_document")
  _chat_files.delete(where={
    "$and": [
      {"session_id": str(session_id)},
      {"file_id": str(file_id)}
    ]
  })


def retrieve_documents(session_id: UUID, query: str, k:int = 4):
  logger.info(f"retrieve_documents: {session_id}")
  results = _chat_files.similarity_search(
    query,
    k=k,
    filter={"session_id": str(session_id)}
  )
  return results
