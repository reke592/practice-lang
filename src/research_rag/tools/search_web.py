from langchain.messages import AIMessage
from langchain_core.documents import Document
from utils.logger import getLogger
from ..state import State
from .common import  text_splitter, compressor
import requests
import os


_logger = getLogger(__name__)


def download_file(url: str, save_path: str):
    if os.path.exists(save_path):
        _logger.info(f"File already exists: {save_path}")
        return True
    try:
        _logger.info(f"Downloading {url}")
        with requests.get(url, stream=True, timeout=15) as r:
            r.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    except Exception as e:
        _logger.error(f"Error downloading {url}: {e}")
        return False


def search_web(state: State):
  """Search the web for information."""
  query=state["messages"][-1].content
  hypothesis=state["hypothesis"]
  citations=set()
  _logger.info(f"Searching the web for: {query}")
  url=f"http://host.docker.internal:8080/search"
  params = {
     "q": query, 
     "format": "json",
    #  "engines": "duckduckgo,brave,google"
  }
  try:
    response = requests.get(url, params, timeout=10)
    results = response.json().get("results", [])
    documents: list[Document] = []
    for r in results:
      content = f"{r['title']}\n{r['content']}"
      chunks = text_splitter.create_documents([content], metadatas=[{"source": r["url"]}])
      documents.extend(chunks)

    _logger.info(f"Retrieved {len(documents)} documents from web search")

    relevant_docs = compressor.compress_documents(documents, hypothesis or query)
    _logger.info(f"{len(relevant_docs)} documents passed the relevance threshold after compression")

    serialized_docs=[]
    for doc in relevant_docs:
      serialized_docs.append({"page_content": doc.page_content, "source": doc.metadata.get("source")})
      citations.add(doc.metadata.get("source"))

    # serialized_docs = [{"page_content": doc.page_content, "source": doc.metadata.get("source")} for doc in relevant_docs]

    return {
      "documents": serialized_docs,
      "citations": list(citations),
      "messages": [
        AIMessage(
          content=f"Retrieved {len(relevant_docs)} relevant documents from the web.",
        )
      ]
    }
    
  
  except Exception as e:
    _logger.error(f"Error fetching web data: {str(e)}")
    return {
      "citations": list(citations),
      "messages": [
        AIMessage(
          content=f"Failed to retrieve information from the web: {str(e)}",
        )
      ]
    }
