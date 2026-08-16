import os
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document, BaseDocumentCompressor
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_community.document_compressors.flashrank_rerank import FlashrankRerank
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_core.retrievers import RetrieverLike
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
from flashrank import Ranker

from logger import getLogger
import environment as env

_logger = getLogger(__name__)

def get_embedding_func():
  if env.EMBED_PROVIDER=="ollama":
    return OllamaEmbeddings(
      model=env.EMBED_PROVIDER_MODEL, 
      base_url=env.EMBED_PROVIDER_BASE_URL
    )
  if env.EMBED_PROVIDER=="openai":
    return OpenAIEmbeddings(
      model=env.EMBED_PROVIDER_MODEL,
      api_key=env.EMBED_PROVIDER_API_KEY,
      base_url=env.EMBED_PROVIDER_BASE_URL
    )
  raise RuntimeError("EMBED_PROVIDER not supported.")

cache_dir = env.DATA_DIR / 'flashrank'

cache_dir.mkdir(parents=True, exist_ok=True)

ranker_client = Ranker(model_name=env.RANKER_MODEL, cache_dir=str(cache_dir))

# here we use the top 6 because we adjust the embedding to nomicV2 which is limitted to 512 tokens
compressor = FlashrankRerank(client=ranker_client, top_n=6)

embedding_func = get_embedding_func()

text_splitter = RecursiveCharacterTextSplitter(
  # given: nomic-embed-text-v2-moe has hard limit 512 tokens
  # we need to make this lower to support non-english characters
  # here we use str len as length_function, to make the splitter model agnostic
  chunk_size=1000,
  chunk_overlap=200,
  length_function=len
)

_logger.info(f"using embed_model: {env.EMBED_PROVIDER_MODEL}")
_logger.info(f"using rank_model: {env.RANKER_MODEL}")


async def read_path_to_docs(folder_path: str) -> list[tuple[List[Document], str]]:
  _logger.info(f"read_path_to_docs: {folder_path}")
  documents = []
  for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)
    if filename.endswith(".pdf"):
      loader = PyPDFLoader(file_path)
    elif filename.endswith(".docx"):
      loader = Docx2txtLoader(file_path)
    else:
      raise TypeError("Unsupported file type")
    documents.extend((await loader.aload(), filename))
  return documents


async def read_path_to_doc(abspath: str) -> tuple[List[Document], str]:
  _logger.info(f"read_path_to_doc: {abspath}")
  if abspath.endswith(".pdf"):
    loader = PyPDFLoader(abspath)
  elif abspath.endswith(".docx"):
    loader = Docx2txtLoader(abspath)
  else:
    raise TypeError(f"Unsupported file type: {os.path.basename(abspath)}")
  docs = await loader.aload()
  return (docs, os.path.basename(abspath))


def setup_reranker(base_retriever: RetrieverLike, compressor: BaseDocumentCompressor):
  """
  wraps vector store to filter noise
  """
  compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=base_retriever
  )
  return compression_retriever
