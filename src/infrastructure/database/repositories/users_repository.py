import random

from environment import DATA_DIR
from infrastructure.database.client import DatabaseClient
from utils.passwords import hash_password
from logger import getLogger

_logger = getLogger(__name__)

class UsersRepository:

  def __init__(self, db: DatabaseClient):
    self.db = db

  async def ensure_admin_exists(self):
    """
    Initialize the admin user in the database if it doesn't exist.
    """
    _logger.info("ensure_admin_exists")
    async with self.db.unit_of_work() as uow:
      # check if any admin exists
      sql = 'SELECT id FROM users WHERE is_admin = TRUE AND is_active = True LIMIT 1'
      existing_admin = await uow.fetch_one(sql)
      if not existing_admin:
        # create admin user
        sql = '''
        INSERT INTO users (username, email, password_hash, is_admin)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (username) DO NOTHING
        RETURNING id
        '''
        
        # generate random password
        random_plain = random.getrandbits(128).to_bytes(16, 'big').hex()
        hashed_password = hash_password(random_plain)
        
        # write the admin password to file for reference
        password_file_path = DATA_DIR / "admin_password.txt"
        with open(password_file_path, "w") as f:
          f.write(random_plain)
        
        new_record = await uow.fetch_one(sql, ('admin', '', hashed_password, True))
        if new_record:
          print(f"admin user created. see {password_file_path}")
