import sqlite3
from contextlib import contextmanager
from utils.logger import getLogger
from models.chat import ChatMessage
from sqlite3 import Cursor
from uuid import uuid4, UUID
from datetime import datetime

DB_FILE="var/data.db"
TBL_CHAT_SESSIONS="chat_sessions"
TBL_CHAT_MESSAGES="chat_messages"

logger=getLogger(__name__)

@contextmanager
def get_cursor():
  conn = sqlite3.connect(DB_FILE)
  conn.row_factory = sqlite3.Row
  cursor = conn.cursor()
  try:
    yield cursor
    if conn.in_transaction:
      conn.commit()
  except Exception as e:
    logger.error(e)
    if conn.in_transaction:
      conn.rollback()
    raise e
  finally:
    cursor.close()
    conn.close()


def init_tables():
  logger.info("init_tables")
  with get_cursor() as cursor:
    cursor.execute(f'''
      CREATE TABLE IF NOT EXISTS {TBL_CHAT_SESSIONS} (
        id TEXT PRIMARY KEY,
        topic TEXT,
        created_at DATETIME
      )
    ''')

    cursor.execute(f'''
      CREATE TABLE IF NOT EXISTS {TBL_CHAT_MESSAGES} (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        role TEXT,  -- 'human', 'ai'
        content TEXT,
        metadata TEXT,  -- store extra json (tokens, model name, etc...)
        created_at DATETIME,
        FOREIGN KEY(session_id) REFERENCES {TBL_CHAT_SESSIONS}(id)
      )
    ''')


def check_session_id(session_id: UUID, cursor: Cursor) -> bool:
  """
  check if the session id exist in database
  """
  logger.info(f"check_session_id {session_id}")
  params = (str(session_id) if session_id else "",)
  cursor.execute(f'''
                  SELECT id FROM {TBL_CHAT_SESSIONS} 
                  WHERE id = ?''', 
                  params)
  result = cursor.fetchone() 

  return result is not None


def create_session(topic: str, cursor: Cursor) -> UUID:
  f"""
  insert new record in {TBL_CHAT_SESSIONS} with the following topic and return the session_id
  """
  id = uuid4()
  logger.info(f"create_session {id}, topic: {topic}")
  cursor.execute(f"""
                 INSERT INTO {TBL_CHAT_SESSIONS}(id, topic, created_at)
                 VALUES(?, ?, ?)
                 """,
                 (str(id), topic, datetime.now()))
  return id
  

def save_messages(session_id: UUID, messages: list[tuple[str,str]], cursor: Cursor):
  f"""
  save new messages in history
  """
  logger.info(f"save_messages {session_id}")
  data_to_insert = [
    (str(session_id), m['role'], m['content'], datetime.now())
    for m in messages
  ]
  cursor.executemany(f"""
                      INSERT INTO {TBL_CHAT_MESSAGES}(session_id, role, content, created_at)
                      VALUES(?, ?, ?, ?)
                      """,
                      data_to_insert)

def get_chat_history(session_id: UUID, cursor: Cursor) -> list[ChatMessage]:
  """
  get existing chat messages in given session
  """
  
  logger.info(f"get_chat_history {session_id}")
  params = (str(session_id),)
  cursor.execute(f'''
                SELECT role, content, created_at 
                FROM {TBL_CHAT_MESSAGES} 
                WHERE session_id=?
                ''', 
                params)
    
  rows = cursor.fetchall()
  
  logger.info(f"loaded history: {len(rows)}")

  return [
    ChatMessage(
      role=row['role'],
      content=row['content'],
      timestamp=row['created_at'] if row['created_at'] else ""
    ) for row in rows
  ]
