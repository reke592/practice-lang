from typing import List

from psycopg.types.json import Jsonb

from langchain_core.callbacks import AsyncCallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever

from infrastructure.database.client import DatabaseClient
from utils.embeddings import read_path_to_doc, setup_reranker, compressor, embedding_func, text_splitter
from logger import getLogger

_logger = getLogger(__name__)


class DocumentsRetriever(BaseRetriever):
  user_id: int
  db: DatabaseClient
  embedding_func: Embeddings

  k: int = 20
  """the top number of chunks to retrieve for relevance ranking."""
  
  n: int = 2
  """retrieves the top n documents based on top k chunks"""

  class Config:
    arbitrary_types_allowed = True

  # LangChain will automatically use _aget_relevant_documents for sync calls 
  # if you don't define _get_relevant_documents, but it's safer to provide a placeholder
  def _get_relevant_documents(self, query: str, *, run_manager):
      raise NotImplementedError("This retriever only supports async calls.")

  async def _aget_relevant_documents(self, query: str, *, run_manager: AsyncCallbackManagerForRetrieverRun) -> List[Document]:
    # async with self.db.get_connection() as conn:
    _logger.info('_aget_relevant_documents')
    prefixed_query = f"search_query: {query}"
    query_embedding = await self.embedding_func.aembed_query(prefixed_query)
    async with self.db.get_connection() as conn:
      await conn.execute(f'SET LOCAL hnsw.ef_search = {max(self.k * 2, 40)}')
      # here we need to get more rows for the ranker to compute the most relevant document
      sql = '''
      WITH best_match AS (
        SELECT d.id, (de.embedding <=> %(embedding)s::vector) AS distance
        FROM users u
        INNER JOIN documents d ON d.created_by_id = u.id
        INNER JOIN document_embeddings de ON de.document_id = d.id
        WHERE u.id = %(user_id)s
          AND (de.embedding <=> %(embedding)s::vector) < 1
          ORDER BY (de.embedding <=> %(embedding)s::vector) ASC
          LIMIT %(k)s
      ),
      target_docs AS (
        SELECT id, MIN(distance) AS best_chunk_distance
        FROM best_match
        GROUP BY id
        ORDER BY best_chunk_distance ASC
        LIMIT %(n)s -- here we look for top n documents.
      )
      SELECT 
        d.id, 
        d.title,
        de.content, 
        de.metadata, 
        (de.embedding <=> %(embedding)s::vector) as distance
      FROM document_embeddings de
      INNER JOIN documents d ON de.document_id = d.id
      WHERE d.id IN (SELECT id FROM target_docs)
      ORDER BY distance ASC
      LIMIT %(k)s  -- we fetch more rows, let the ranker do the relevance check.
      '''
      cursor = await conn.execute(sql, {
        'user_id': self.user_id,
        'embedding': query_embedding,
        'k': max(self.k * 2, 40),
        'n': self.n
      })
      
      rows = await cursor.fetchall()
    
    retrieved_docs = [
      Document(
        id=r['id'], 
        page_content=r['content'], 
        metadata=(
          r['metadata'] | 
          {
            'document_id': r['id'],
            'title': r['title'],
            'distance': r['distance']
          }
        )
      ) 
      for r in rows
    ]
    # for doc in retrieved_docs:
    #   print(doc.metadata)
    return retrieved_docs


class DocumentsRepository:

  def __init__(self, db: DatabaseClient):
    self.db = db

  async def save_document(self, user_id: int, title: str, file_path: str) -> int:
    """
    Save new document and its embeddings to the database. The document is split into chunks, and each chunk is embedded and stored in the document_embeddings table.
    Returns the new document's id.
    """
    _logger.info(f'save_document: {file_path}')

    async with self.db.unit_of_work() as uow:
      # load file contents
      documents, filename = await read_path_to_doc(file_path)
      
      # create document metadata
      sql = '''
      INSERT INTO documents(created_by_id, title, file_path)
      VALUES (%s, %s, %s)
      RETURNING id
      '''
      new_record = await uow.fetch_one(sql, (user_id, title, file_path))

      # split document into chunks
      chunks = text_splitter.split_documents(documents)

      # add nomic-v2 prefix for each chunk and save the vector embedding to the database
      for chunk in chunks:
        prefixed_content = f"search_document: {chunk.page_content}"
        vector = await embedding_func.aembed_query(prefixed_content)
        metadata = {
           'user_id': user_id,
           'document_id': new_record['id'],
           'title': title,
           'page': chunk.metadata.get('page', '')
        }
        sql='''
        INSERT INTO document_embeddings(document_id, created_by_id, content, embedding, metadata)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        '''
        await uow.fetch_one(sql, (new_record['id'], user_id, chunk.page_content, vector, Jsonb(metadata)))

      # finally return the new record id
      return new_record['id']


  async def delete_document(self, user_id: int, document_id: int) -> bool:
    """
    Deletes a document and its associated embeddings from the database.
    Returns True if the document was deleted, False otherwise.
    """
    _logger.info(f'delete_document: {document_id}')
    async with self.db.unit_of_work() as uow:
      sql = '''
      DELETE FROM documents
      WHERE id = %s AND created_by_id = %s
      RETURNING id
      '''
      deleted_record = await uow.fetch_one(sql, (document_id, user_id))

      # delete associated embeddings
      sql = '''
      DELETE FROM document_embeddings
      WHERE document_id = %s AND user_id = %s
      '''
      await uow.execute(sql, (document_id, user_id))
      
      return True if deleted_record['id'] else False


  async def search_for_relevant_documents(
    self,
    user_id: int,
    query: str, 
  ) -> list[dict]:
    """
    Search for relevant documents based on the query. The documents are ranked by relevance using a reranker.
    Returns a list of dictionaries containing the metadata and page content of the relevant documents.
    """
    _logger.info(f'search_for_relevant_documents: {query}')
    base_retriever = DocumentsRetriever(user_id=user_id, db=self.db, embedding_func=embedding_func)
    ranker = setup_reranker(base_retriever=base_retriever, compressor=compressor)
    relevant_docs = await ranker.ainvoke(query)
    results = []
    meta_keys = {'relevance_score', 'distance', 'page', 'title', 'document_id'}
    for doc in relevant_docs:
        clean_metadata = {}
        for k, v in doc.metadata.items():
            if k in meta_keys:
                clean_metadata[k] = v.item() if hasattr(v, 'item') else v
        results.append(
            {
                'metadata': clean_metadata,
                'page_content': doc.page_content
            }
        )
    return results
