from fastapi import APIRouter

from app.core.redis_client import get_redis_client
from app.leaderboard.constants import TILES_OWNED_LEADERBOARD_KEY

router = APIRouter()


@router.get("/top-users")
def top_users() -> dict:
    redis_client = get_redis_client()
    rows = redis_client.zrevrange(TILES_OWNED_LEADERBOARD_KEY, 0, 9, withscores=True)

    return {
        "users": [
            {"user_id": int(user_id), "tiles_owned": int(score)}
            for user_id, score in rows
        ]
    }
