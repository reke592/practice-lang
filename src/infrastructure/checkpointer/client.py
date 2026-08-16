from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool
from psycopg import AsyncConnection
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

import environment as env
from logger import getLogger

_logger = getLogger(__name__)

_checkpointer_client: BaseCheckpointSaver[str] | None = None
_checkpointer_pool: AsyncConnectionPool[AsyncConnection[DictRow]] | None = None

safe_serde = JsonPlusSerializer(
  allowed_msgpack_modules=[
    ('agent.supervisor', 'McpSkill')
  ]
)

def get_postgre_conninfo():
  return f"dbname={env.CHECKPOINTER_DB_NAME} user={env.CHECKPOINTER_DB_USER} password={env.CHECKPOINTER_DB_PASSWORD} host={env.CHECKPOINTER_DB_HOST} port={env.CHECKPOINTER_DB_PORT}"


def get_checkpointer() -> BaseCheckpointSaver[str]:
  global _checkpointer_client  
  if not _checkpointer_client:
    raise RuntimeError("checkpointer not yet initialized, call checkpointer_setup first!")
  return _checkpointer_client


async def checkpointer_setup():
  """initialize the global checkpointer client"""
  global _checkpointer_client
  global _checkpointer_pool
  checkpointer_type = env.CHECKPOINTER_CLIENT.lower().strip()
  
  if checkpointer_type == "memory":
    _checkpointer_client = MemorySaver(
      serde=safe_serde
    )
    return _checkpointer_client

  if checkpointer_type == "postgre":
    _logger.info("initializing...")
    # the actual checkpointer to use in graph
    _checkpointer_pool = AsyncConnectionPool(
      conninfo=get_postgre_conninfo(),
      min_size=2,
      max_size=20,
      open=False,  # don't open in constructor,
      kwargs={"row_factory": dict_row}
    )

    await _checkpointer_pool.open()

    _checkpointer_client = AsyncPostgresSaver(_checkpointer_pool, serde=safe_serde)
    await _checkpointer_client.setup()
    return _checkpointer_client
  
  raise ValueError(f"checkpointer type {checkpointer_type} not supported.")


async def checkpointer_close():
  """close the checkpointer connection"""
  global _checkpointer_pool
  checkpointer = get_checkpointer()
  
  if not checkpointer:
    return
  
  if isinstance(checkpointer, AsyncPostgresSaver):
    _logger.info("closing connection...")
    await checkpointer.conn.close()

  if _checkpointer_pool:
    _logger.info("closing pool...")
    await _checkpointer_pool.close()


async def delete_checkpoint(thread_id: str):
  """delete a checkpoint by thread_id"""
  get_checkpointer().delete_thread(thread_id=thread_id)
  