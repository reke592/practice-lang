from pathlib import Path
from utils.environment import DATA_DIR, LLAMA_EMBED_MODEL, LLAMA_URL, RANKER_MODEL, RANKER_THRESHOLD, TEMP_DIR
from langchain_ollama import OllamaEmbeddings
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_compressors import FlashrankRerank
from flashrank import Ranker

VAR_DATA_DIR = Path(DATA_DIR) / "local-first-rag"
VAR_DATA_DIR.mkdir(exist_ok=True, parents=True)
CHROMA_DB_FILE = f'{VAR_DATA_DIR}/chroma_db'
CHROMA_COLLECTION_NAME = "construction_materials"
DOWNLOADED_FILES = VAR_DATA_DIR / "downloads"
DOWNLOADED_FILES.mkdir(exist_ok=True, parents=True)

embedding_function = OllamaEmbeddings(model=LLAMA_EMBED_MODEL, base_url=LLAMA_URL)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len
)
flashrank_client = Ranker(model_name=RANKER_MODEL, cache_dir=TEMP_DIR)
compressor = FlashrankRerank(client=flashrank_client, top_n=7, score_threshold=RANKER_THRESHOLD)
