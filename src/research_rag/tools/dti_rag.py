import os
import re
import requests
import asyncio
import pandas as pd
from langchain_classic.retrievers import ContextualCompressionRetriever
from datetime import datetime
from typing import List
from pathlib import Path
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, CSVLoader
from langchain_core.documents import Document
from langchain_chroma import Chroma
from playwright.async_api import async_playwright
from langchain.tools import tool, ToolRuntime
from research_rag.tools.common import CHROMA_DB_FILE, VAR_DATA_DIR, compressor, embedding_function, text_splitter
from utils.environment import RANKER_THRESHOLD
from utils.llm import Context
from utils.logger import getLogger
from concurrent.futures import ThreadPoolExecutor

LOCAL_DATA_DIR = Path(f"{VAR_DATA_DIR}/dti_rag")
CHROMA_COLLECTION_NAME = "dti_rag"

_logger = getLogger(__name__)

# Initialize store
_chroma = Chroma(
  collection_name=CHROMA_COLLECTION_NAME, # Keep a consistent name
  embedding_function=embedding_function,
  persist_directory=CHROMA_DB_FILE
)

def parse_file_links(link: str, extensions: list[str]) -> str:
    lower_link = link.lower()
    for ext in extensions:
        if ext in lower_link:
            url = link.split(ext)[0] + ext
            match = re.split(r'http[s]?://', url)
            if len(match) > 1:
                if "http://" + match[1] in url:
                    return "http://" + match[1]
                elif "https://" + match[1] in url:
                    return "https://" + match[1]
    return ""


def is_valid_link(href: str, valid_extensions: list[str], valid_content_types: list[str]) -> bool:
    if not href or not any(ext in href.lower() for ext in valid_extensions):
        return False
    response = requests.head(href, allow_redirects=True)
    content_type = response.headers.get('Content-Type', '')
    length = response.headers.get('Content-Length', 'unknown')
    length = int(length) / 1024 / 1024 if length != 'unknown' else 'unknown'  # Convert to MB
    if content_type in valid_content_types:
        _logger.info(f"size: {length:.2f} MB, url: {href}")
        return True
    return False


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


class ExcelToJsonDocLoader():    
    def __init__(self, path: str):
        self.file_path = path

    def load(self) -> list[Document]:
        # sheet_name=None reads ALL sheets into a dict {sheet_name: dataframe}
        all_sheets = pd.read_excel(self.file_path, sheet_name=None)
        
        documents = []
        
        for sheet_name, df in all_sheets.items():
            # skip headers
            header_row_index = df.apply(lambda x: x.notnull().sum(), axis=1).idxmax()
            header_row_idx = int(header_row_index)
            df.columns = df.iloc[header_row_idx] # Set the columns to that row's values
            df = df.iloc[header_row_idx + 1:].reset_index(drop=True) # Data starts after
            # Clean data per sheet
            df = df.dropna(how='all').fillna("N/A")
            splits = []
            # Metadata is key for FlashRank reranking and filtering
            metadata = { 
                "source": self.file_path,
                "page": sheet_name
            }

            # Optimization: If the sheet is empty after cleaning, skip it
            if df.empty:
                continue

            for _, row in df.iterrows():
                row_dict = row.to_dict()
                parts = []
                
                for k, v in row_dict.items():
                    # 1. Clean up key and value
                    k_str = str(k) if k is not None else ""
                    v_str = str(v).strip()
                    
                    # 2. Skip 'Unnamed' or empty headers
                    if not k_str or k_str.startswith("Unnamed"):
                        continue
                        
                    # 3. Skip 'N/A' or empty values (case-insensitive)
                    if v_str.upper() in ["N/A", "NAN", "NONE", "NULL", "", "0"]:
                        continue

                    # 4. match if the k_str is a date so we can include details to help the model
                    date_match = re.search(r'\d{4}-\d{2}-\d{2}', k_str)
                    if date_match:
                        k_str = f"Price as of {date_match.group(0)}"
                        
                    parts.append(f"{k_str}: {v_str}")

                splits.append(" ".join(parts))
            
            documents.append(Document(page_content="\n".join(splits), metadata=metadata))
            #Log the first few splits for debugging
            _logger.info("\n".join(splits[0:3]))
        return documents


def load_documents(folder_path: str) -> List[Document]:
    documents = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif filename.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            loader = ExcelToJsonDocLoader(file_path)
        elif filename.endswith(".csv"):
            loader = CSVLoader(file_path)
        else:
            _logger.error(f"Unsupported file type: {filename}")
            continue
        _logger.info(f"Loading document: {filename}")
        documents.extend(loader.load()) 
    return documents


async def scrape_dti_s3(year: int) -> list[str]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        sources = [
            f"https://dtiwebfiles.s3.ap-southeast-1.amazonaws.com/e-Presyo/Monthly%20Monitored%20Prevailing%20Price/Construction%20Materials%20/index.html?prefix=e-Presyo/Monthly%20Monitored%20Prevailing%20Price/Construction%20Materials%20",
            f"https://dtiwebfiles.s3.ap-southeast-1.amazonaws.com/e-Presyo/Monthly%20Monitored%20Prevailing%20Price/Construction%20Materials%20/index.html?prefix=e-Presyo/Monthly%20Monitored%20Prevailing%20Price/Construction%20Materials%20/{year}/"
        ]
        valid_content_types = [
            "application/pdf", 
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            "application/vnd.ms-excel",
            "text/csv"
        ]
        valid_extensions = [".pdf", ".xlsx", ".xls", ".csv"]
        file_urls = []

        for url in sources:
            # Navigate to DTI link
            _logger.info(f"Navigating to {url}")
            await page.goto(url)

            # Wait for the file table to load
            await page.wait_for_selector("table")
            
            # Extract all links that contain "pdf" or "xlsx"
            links = await page.query_selector_all("a")
            _logger.info(f"Scanning {len(links)} links on the page.")

            for link in links:
                href = await link.get_attribute("href")
                # _logger.info(f"Checking link: {href}")
                if href:
                    if is_valid_link(href, valid_extensions, valid_content_types):
                        file_urls.append(href)
                    else:
                        query_param_url=parse_file_links(href, extensions=valid_extensions)
                        if is_valid_link(query_param_url, valid_extensions, valid_content_types):
                            file_urls.append(query_param_url)
        
        _logger.info(f"Found {len(file_urls)} data files with valid content-type for year {year}.")
        # for f in file_urls:
        #     _logger.info(f"Direct Link: {f}")
            
        await browser.close()
        LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)

        for url in file_urls:
            download_file(url, f"{LOCAL_DATA_DIR}/{url.split('/')[-1]}")

        return file_urls


def setup_reranker(base_retriever) -> ContextualCompressionRetriever:
    """
    wraps vector store to filter noise
    """
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=base_retriever
    )
    return compression_retriever


async def retrieve_relevant_documents(query: str, k:int = 100) -> list[Document]:
    """
    use ContextualCompressionRetriever to return the list of relevant documents.
    """
    _logger.info(f"retrieve_relevant_documents: {query}")
    search_kwargs={
        "k": k, 
    }
    retriever = setup_reranker(base_retriever=_chroma.as_retriever(search_kwargs=search_kwargs))
    # retriever = _chroma.as_retriever(search_kwargs=search_kwargs)
    results = await retriever.ainvoke(input=query)
    relevant_docs = [
    doc for doc in results 
        if (doc.metadata.get("relevance_score") or 0) >= RANKER_THRESHOLD
    ]
    for i, doc in enumerate(relevant_docs):
        score = doc.metadata.get("relevance_score") or doc.metadata.get("score")
        _logger.info(f"Doc: {i} | Score: {score} | Source: {doc.metadata.get('source')}")
    return relevant_docs


async def update_dti_s3_vectore_store() -> str:
    year = datetime.now().year
    _logger.info(f"Scraping DTI S3 for year: {year}")
    
    try:
        file_urls = await scrape_dti_s3(year)
        
        # 1. Parallelize File Loading (CPU Intensive)
        # Using a ThreadPool to keep the event loop free
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            documents = await loop.run_in_executor(
                pool, lambda: load_documents(f"{LOCAL_DATA_DIR}")
            )

        all_splits = []
        processed_sources = set()

        # 2. Bulk Preparation (Avoid logic inside the DB loop)
        for doc in documents:
            source = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page", "unknown")
            
            # # Use the atomic rows directly (skipping the heavy splitter if possible)
            # # If you still need the splitter, it's faster to do it in a batch
            splits = text_splitter.split_documents([doc])
            
            for split in splits:
                split.metadata["source"] = source
                split.metadata["page"] = page
            
            all_splits.extend(splits)
            processed_sources.add((source, page))

        # 3. Bulk Delete
        # Deleting in one go is much faster than per-file
        for source, page in processed_sources:
            _chroma.delete(where={
                "$and": [{"source": source}, {"page": page}]
            })

        # 4. Bulk Add with Chunking
        # Chroma performs significantly better with chunks of 500-1000
        batch_size = 2500
        total = range(0, len(all_splits), batch_size)
        for i in total:
            batch = all_splits[i : i + batch_size]
            _chroma.add_documents(batch)
            _logger.info(f"Saved {i//batch_size + 1}/{len(total)}")

        return "\n".join(file_urls)

    except Exception as e:
        _logger.error(f"Error in update_vectore_store: {e}")
        return f"An error occurred: {e}"


@tool
async def search_material_prices(query: str, context: ToolRuntime[Context]) -> str:
    """Search for construction material prices in the local vector store."""
    search_results = await retrieve_relevant_documents(query)
    _logger.info(f"Found {len(search_results)} search results for query: {query}")
    string_results = []
    for doc in search_results:
        source = doc.metadata.get('source', 'unknown')
        string_results.append(f"Source: {source}\nContent: {doc.page_content}")
    _logger.info("\n\n".join(string_results))
    return "\n\n".join(string_results) if search_results else "[No data]"
