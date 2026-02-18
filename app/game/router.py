import logging

from fastapi import APIRouter, Depends, HTTPException, status
from redis.exceptions import RedisError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.college.models import College
from app.core.redis_client import get_redis_client
from app.core.security import enforce_rate_limit
from app.database.session import get_db
from app.game.models import HexTile
from app.game.schemas import ClaimTileRequest
from app.game.service import CLAIM_COST, has_adjacent_owned_tile
from app.leaderboard.constants import TILES_OWNED_LEADERBOARD_KEY

router = APIRouter()
logger = logging.getLogger("steprealm.game")


@router.get("/grid")
def get_grid(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    tiles = db.query(HexTile).order_by(HexTile.r.asc(), HexTile.q.asc()).all()
    return {
        "current_user_id": current_user.id,
        "tiles": [
            {
                "id": tile.id,
                "q": tile.q,
                "r": tile.r,
                "owner_id": tile.owner_id,
            }
            for tile in tiles
        ],
    }


@router.post("/claim")
def claim_tile(payload: ClaimTileRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    enforce_rate_limit(scope="claim_tile", subject_id=current_user.id, limit=10, window_seconds=10)
    logger.info(
        "tile_claim_attempt",
        extra={"user_id": current_user.id, "q": payload.q, "r": payload.r},
    )
    total_tiles_owned = 0
    with db.begin():
        user = db.query(User).filter(User.id == current_user.id).with_for_update().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        tile = db.query(HexTile).filter(HexTile.q == payload.q, HexTile.r == payload.r).with_for_update().first()
        if not tile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tile not found")
        if tile.owner_id is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tile is already owned")

        if user.mana < CLAIM_COST:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough mana")

        if not has_adjacent_owned_tile(db, user.id, payload.q, payload.r):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must claim an adjacent tile")

        user.mana -= CLAIM_COST
        tile.owner_id = user.id
        if user.college_id is not None:
            college = db.query(College).filter(College.id == user.college_id).with_for_update().first()
            if college:
                college.total_tiles += 1
        total_tiles_owned = db.query(func.count(HexTile.id)).filter(HexTile.owner_id == user.id).scalar() or 0

    db.refresh(user)
    db.refresh(tile)
    try:
        get_redis_client().zadd(TILES_OWNED_LEADERBOARD_KEY, {str(user.id): total_tiles_owned})
    except RedisError:
        logger.exception("leaderboard_update_failed", extra={"user_id": user.id})

    logger.info(
        "tile_claim_success",
        extra={"user_id": user.id, "tile_id": tile.id, "q": tile.q, "r": tile.r, "mana": user.mana},
    )

    return {
        "tile_id": tile.id,
        "q": tile.q,
        "r": tile.r,
        "owner_id": tile.owner_id,
        "mana": user.mana,
    }
