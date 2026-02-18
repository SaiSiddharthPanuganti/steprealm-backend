from fastapi import HTTPException, status
from redis.exceptions import RedisError

from app.core.redis_client import get_redis_client


def enforce_rate_limit(*, scope: str, subject_id: int, limit: int, window_seconds: int) -> None:
    key = f"ratelimit:{scope}:{subject_id}"
    redis_client = get_redis_client()

    try:
        current = redis_client.incr(key)
        if current == 1:
            redis_client.expire(key, window_seconds)
    except RedisError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Security service unavailable")

    if current > limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")
