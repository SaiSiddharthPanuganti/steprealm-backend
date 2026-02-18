import os
from functools import lru_cache

from redis import Redis


@lru_cache
def get_redis_client() -> Redis:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return Redis.from_url(redis_url, decode_responses=True)
