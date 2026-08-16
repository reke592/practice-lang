import contextlib
from typing import AsyncGenerator, AsyncIterator, LiteralString
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

from environment import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from logger import getLogger

_logger = getLogger(__name__)

DB_CONFIG = f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}"

class UnitOfWork:
  def __init__(self, connection: AsyncConnection):
    self.connection = connection
    self.transaction = None
  
  async def __aenter__(self):
    self.transaction = self.connection.transaction()
    await self.transaction.__aenter__()
    return self

  async def __aexit__(self, exc_type, exc, tb):
    # If an exception occurred, psycopg handles the rollback automatically
    # within the transaction context manager.
    if self.transaction:
      await self.transaction.__aexit__(exc_type, exc, tb)

  async def execute(self, sql: LiteralString, params: tuple | None = None):
    """Execute query"""
    return await self.connection.execute(sql, params)
  
  async def fetch_one(self, sql: LiteralString, params: tuple | None = None):
    cursor = await self.connection.execute(sql, params)
    return await cursor.fetchone()


class DatabaseClient:
  def __init__(self):
    self.pool: AsyncConnectionPool | None = None
  
  async def connect(self):
    if not self.pool:
      _logger.info("initializing...")
      self.pool = AsyncConnectionPool(
        conninfo=DB_CONFIG,
        min_size=2,
        max_size=10,
        kwargs={"row_factory": dict_row},
        open=False  # don't open in constructor
      )
      # ensure pool is ready
      await self.pool.open()
  
  async def disconnect(self):
    if self.pool:
      _logger.info("closing...")
      await self.pool.close()

  @contextlib.asynccontextmanager
  async def get_connection(self) -> AsyncGenerator[AsyncConnection, None]:
    if not self.pool:
      await self.connect()

    if self.pool:
      async with self.pool.connection() as conn:
        yield conn

  @contextlib.asynccontextmanager
  async def unit_of_work(self) -> AsyncGenerator[UnitOfWork, None]:
    if not self.pool:
      raise RuntimeError("DatabaseClient is not connected. Call connect() first.")
    
    async with self.pool.connection() as conn:
      async with UnitOfWork(conn) as uow:
        yield uow


db_client = DatabaseClient()
