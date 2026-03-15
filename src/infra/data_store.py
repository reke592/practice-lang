import sqlite3
from contextlib import contextmanager
from utils.environment import DATA_DIR
from utils.logger import getLogger
from models.chat import ChatMessage, ChatSession, ChatFile
from sqlite3 import Cursor
from uuid import uuid4, UUID
from datetime import datetime


DB_FILE=f"{DATA_DIR}/data.db"
TBL_CHAT_SESSIONS="chat_sessions"
TBL_CHAT_MESSAGES="chat_messages"
TBL_CHAT_FILES="chat_files"

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
    cursor.execute(f'''
      CREATE TABLE IF NOT EXISTS {TBL_CHAT_FILES} (
        file_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        source TEXT,
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


def create_session(id: UUID, topic: str, cursor: Cursor) -> UUID:
  f"""
  insert new record in {TBL_CHAT_SESSIONS} with the following topic and return the session_id
  """
  logger.info(f"create_session {id}, topic: {topic}")
  cursor.execute(f"""
                 INSERT INTO {TBL_CHAT_SESSIONS}(id, topic, created_at)
                 VALUES(?, ?, ?)
                 """,
                 (str(id), topic, datetime.now()))
  return id
  

def save_messages(session_id: UUID, messages: list[dict], cursor: Cursor):
  f"""
  save new messages in history
  """
  logger.info(f"save_messages {session_id}")
  data_to_insert = [
    (str(session_id), m['role'], m['content'], datetime.now(),)
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


def get_chat_sessions(cursor: Cursor) -> list[ChatSession]:
  logger.info("get_sessions")
  cursor.execute(f'''
                  SELECT *
                  FROM {TBL_CHAT_SESSIONS}
                  ''')
  rows = cursor.fetchall()
  return [
    ChatSession(
      session_id=row['id'],
      topic=row['topic']
    )  for row in rows
  ]


def delete_chat_session(session_id: UUID, cursor: Cursor):
  logger.info(f"delete_chat_session {session_id}")
  param = (str(session_id),)
  cursor.execute(f'DELETE FROM {TBL_CHAT_MESSAGES} WHERE `session_id`=?', param)
  cursor.execute(f'DELETE FROM {TBL_CHAT_FILES} WHERE `session_id`=?', param)
  cursor.execute(f'DELETE FROM {TBL_CHAT_SESSIONS} WHERE `id`=?', param)
  

def find_file_id(session_id: UUID, source: str, cursor: Cursor) -> dict:
  cursor.execute(f"""
                  SELECT file_id 
                  FROM {TBL_CHAT_FILES} 
                  WHERE session_id=? 
                  AND source=?""", 
                  (str(session_id), source,))
  existing_file_id = cursor.fetchone()
  return existing_file_id

def save_chat_file(session_id: UUID, source: str, cursor: Cursor) -> ChatFile:
  logger.info(f"save_chat_file {session_id}")
  sesison_str=str(session_id)
  created_at=f"{datetime.now()}"
  existing = find_file_id(session_id=session_id, 
                                  source=source, 
                                  cursor=cursor)
  if not existing:
    params = (sesison_str, source, created_at,)
    cursor.execute(f"""
                        INSERT INTO {TBL_CHAT_FILES}(session_id, source, created_at)
                        VALUES(?, ?, ?)
                        """,
                        params)
  else:
    params = (existing['file_id'], created_at)
    cursor.execute(f"""
                    UPDATE {TBL_CHAT_FILES}
                    SET created_at=?
                    WHERE file_id=?
                    """,
                    params)
  record = find_file_id(session_id=session_id, 
                                source=source, 
                                cursor=cursor)
  return ChatFile(
    file_id=record['file_id'],
    session_id=session_id,
    source=source,
    created_at=created_at
  )
  

def get_chat_files(session_id: UUID, cursor: Cursor) -> list[ChatFile]:
  logger.info("get_chat_files")
  cursor.execute(f'''
                  SELECT *
                  FROM {TBL_CHAT_FILES}
                  WHERE session_id = ?
                  ''',
                  (str(session_id),))
  rows = cursor.fetchall()
  return [
    ChatFile(
      file_id=row['file_id'],
      session_id=row['session_id'],
      source=row['source'],
      created_at=row['created_at']
    )  for row in rows
  ]


def delete_chat_file(session_id: UUID, file_id: int, cursor: Cursor):
  logger.info("delete_chat_file")
  cursor.execute(f'''
                  DELETE FROM {TBL_CHAT_FILES}
                  WHERE session_id=? 
                    AND file_id=?
                  ''',
                  (str(session_id), file_id,))
