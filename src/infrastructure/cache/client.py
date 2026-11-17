from datetime import timedelta

import redis.asyncio as redis
import shared.environment as env
from shared.errors import CancellationError

from shared.logger import getLogger

_logger = getLogger(__name__)

type ExpiryT = int | timedelta

class BaseCacheClient:
  async def connect(self):
    """test client connection"""
    raise NotImplementedError()

  async def disconnect(self):
    """close the connection"""
    raise NotImplementedError()
  
  async def get(self, key: str):
    """get cached value"""
    raise NotImplementedError()
  
  async def set(self, key: str, value: str, ex: ExpiryT | None):
    """set cache value"""
    raise NotImplementedError()

  async def delete(self, *keys: str):
    """delete cached value"""
    raise NotImplementedError()

  async def set_cancellation(self, value: str):
    """set a cancellation token in cache"""
    token = f"abort:{value}"
    await self.set(token, "1", timedelta(minutes=3))

  async def check_cancellation(self, value: str):
    """
    checks the cache database if cancellation token has been set.

    raise CancellationError
    """
    token = f"abort:{value}"
    if await self.get(token):
      await self.delete(token)
      raise CancellationError("Request cancelled.")


class RedisClient(BaseCacheClient):
  def __init__(self, host: str, port: int, username: str, password: str, max_connections: int):
    self.pool = redis.ConnectionPool(
      host=host,
      port=port,
      username=username or None,
      password=password or None,
      max_connections=max_connections
    )
    self.client = redis.Redis(connection_pool=self.pool)

  async def connect(self):
    try:
      await self.client.ping()
      _logger.info("connected.")
    except Exception as e:
      _logger.error(f"can't connect to redis. {e}")

  async def disconnect(self):
    return await self.client.close()

  async def get(self, key: str):
    return await self.client.get(name=key)

  async def set(self, key: str, value: str, ex: ExpiryT | None):
    return await self.client.set(name=key, value=value, ex=ex)

  async def delete(self, *keys: str):
    return await self.client.delete(*keys)


redis_client = RedisClient(
    host=env.REDIS_HOST,
    port=env.REDIS_PORT,
    username=env.REDIS_USER,
    password=env.REDIS_PASSWORD.get_secret_value(),
    max_connections=env.REDIS_MAX_CONNECTION
)