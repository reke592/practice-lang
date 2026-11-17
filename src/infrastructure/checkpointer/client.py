from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool
from psycopg import AsyncConnection
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

import shared.environment as env
from shared.logger import getLogger

_logger = getLogger(__name__)

_checkpointer_client: BaseCheckpointSaver[str] | None = None
_checkpointer_pool: AsyncConnectionPool[AsyncConnection[DictRow]] | None = None

safe_serde = JsonPlusSerializer(
  allowed_msgpack_modules=[
    ('agent.schemas', 'MCPSkill')
  ]
)

def get_postgre_conninfo():
  return f"dbname={env.CHECKPOINTER_DB_NAME} user={env.CHECKPOINTER_DB_USER} password={env.CHECKPOINTER_DB_PASSWORD.get_secret_value()} host={env.CHECKPOINTER_DB_HOST} port={env.CHECKPOINTER_DB_PORT}"


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
    async with _checkpointer_pool.connection() as conn:
      await conn.set_autocommit(True)
      await AsyncPostgresSaver(conn, serde=safe_serde).setup()
    
    _checkpointer_client = AsyncPostgresSaver(_checkpointer_pool, serde=safe_serde)
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
  """delete the entire history by thread_id"""
  _logger.info(f"delete_checkpoint thread_id: {thread_id}")
  get_checkpointer().delete_thread(thread_id=thread_id)

async def delete_turns(thread_id: str, run_id: str):
  """delete a conversation turn in history"""
  client = get_checkpointer()
  if isinstance(client, AsyncPostgresSaver):
    _logger.info(f"delete_turns thread_id: {thread_id}, run_id: {run_id}")
    async with client.conn.connection() as conn:
      async with conn.cursor() as cur:
        # query the checkpoint ids related to the current conversation turn
        sql = """
        SELECT checkpoint_id
        FROM checkpoints
        WHERE thread_id = %s
          AND metadata->>'run_id' = %s
        """
        await cur.execute(sql, (thread_id, run_id))
        
        checkpoint_ids = [ row['checkpoint_id'] for row in await cur.fetchall() ]

        # delete the history
        await cur.execute("""
        DELETE FROM checkpoints
        WHERE thread_id = %s
          AND checkpoint_id = ANY(%s)
        """, (thread_id, checkpoint_ids))

        await cur.execute("""
        DELETE FROM checkpoint_writes
        WHERE thread_id = %s
          AND checkpoint_id = ANY(%s)
        """, (thread_id, checkpoint_ids))
  else:
    _logger.warning(f"delete_turns not supported. Please clear the session history instead.")
