import logging

from fastapi import APIRouter, Depends, HTTPException, status
from redis.exceptions import RedisError
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.sql import tuple_

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.college.models import College
from app.core.redis_client import get_redis_client
from app.core.security import enforce_rate_limit
from app.database.session import get_db
from app.game.models import HexTile
from app.game.schemas import ClaimByLocationRequest, ClaimTileRequest
from app.game.service import (
    CLAIM_COST,
    WALK_CAPTURE_DISTANCE_METERS,
    axial_disk,
    axial_to_boundary,
    axial_to_lat_lng,
    has_adjacent_owned_tile,
    lat_lng_to_axial,
    user_owns_any_tile,
)
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
    claimed = False
    try:
        user, tile, total_tiles_owned, claimed = _claim_tile_tx(
            db=db,
            user_id=current_user.id,
            q=payload.q,
            r=payload.r,
            create_if_missing=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(user)
    db.refresh(tile)
    if claimed:
        _update_leaderboard(user.id, total_tiles_owned)

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


@router.get("/world-grid")
def get_world_grid(
    latitude: float,
    longitude: float,
    radius: int = 3,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if radius < 1 or radius > 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="radius must be between 1 and 8")

    center_q, center_r = lat_lng_to_axial(latitude, longitude)
    coords = axial_disk(center_q, center_r, radius)

    existing_tiles = (
        db.query(HexTile)
        .filter(tuple_(HexTile.q, HexTile.r).in_(coords))
        .all()
    )
    existing_map = {(tile.q, tile.r): tile for tile in existing_tiles}

    tiles_payload: list[dict] = []
    for q, r in coords:
        tile = existing_map.get((q, r))
        center_lat, center_lng = axial_to_lat_lng(q, r)
        boundary = axial_to_boundary(q, r)
        tiles_payload.append(
            {
                "id": tile.id if tile else None,
                "q": q,
                "r": r,
                "owner_id": tile.owner_id if tile else None,
                "center": {"latitude": center_lat, "longitude": center_lng},
                "boundary": [{"latitude": lat, "longitude": lng} for lat, lng in boundary],
            }
        )

    return {
        "current_user_id": current_user.id,
        "center": {"q": center_q, "r": center_r},
        "tiles": tiles_payload,
    }


@router.post("/claim-by-location")
def claim_by_location(
    payload: ClaimByLocationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    enforce_rate_limit(scope="claim_by_location", subject_id=current_user.id, limit=8, window_seconds=30)
    if payload.distance_m < WALK_CAPTURE_DISTANCE_METERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Walk at least {int(WALK_CAPTURE_DISTANCE_METERS)} meters before claiming",
        )

    q, r = lat_lng_to_axial(payload.latitude, payload.longitude)

    logger.info(
        "tile_claim_walk_attempt",
        extra={"user_id": current_user.id, "q": q, "r": r, "distance_m": payload.distance_m},
    )

    total_tiles_owned = 0
    claimed = False
    try:
        user, tile, total_tiles_owned, claimed = _claim_tile_tx(
            db=db,
            user_id=current_user.id,
            q=q,
            r=r,
            create_if_missing=True,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(user)
    db.refresh(tile)

    if claimed:
        _update_leaderboard(user.id, total_tiles_owned)

    center_lat, center_lng = axial_to_lat_lng(tile.q, tile.r)
    boundary = axial_to_boundary(tile.q, tile.r)

    return {
        "claimed": claimed,
        "tile": {
            "id": tile.id,
            "q": tile.q,
            "r": tile.r,
            "owner_id": tile.owner_id,
            "center": {"latitude": center_lat, "longitude": center_lng},
            "boundary": [{"latitude": lat, "longitude": lng} for lat, lng in boundary],
        },
        "mana": user.mana,
    }


def _claim_tile_tx(db: Session, user_id: int, q: int, r: int, create_if_missing: bool) -> tuple[User, HexTile, int, bool]:
    user = db.query(User).filter(User.id == user_id).with_for_update().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    tile = db.query(HexTile).filter(HexTile.q == q, HexTile.r == r).with_for_update().first()
    if not tile:
        if not create_if_missing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tile not found")
        tile = HexTile(q=q, r=r, owner_id=None)
        db.add(tile)
        db.flush()

    if tile.owner_id == user.id:
        total_tiles_owned = db.query(func.count(HexTile.id)).filter(HexTile.owner_id == user.id).scalar() or 0
        return user, tile, total_tiles_owned, False

    if tile.owner_id is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tile is already owned")

    if user.mana < CLAIM_COST:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough mana")

    if user_owns_any_tile(db, user.id) and not has_adjacent_owned_tile(db, user.id, q, r):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must claim an adjacent tile")

    user.mana -= CLAIM_COST
    tile.owner_id = user.id
    if user.college_id is not None:
        college = db.query(College).filter(College.id == user.college_id).with_for_update().first()
        if college:
            college.total_tiles += 1
    total_tiles_owned = db.query(func.count(HexTile.id)).filter(HexTile.owner_id == user.id).scalar() or 0
    return user, tile, total_tiles_owned, True


def _update_leaderboard(user_id: int, total_tiles_owned: int) -> None:
    try:
        get_redis_client().zadd(TILES_OWNED_LEADERBOARD_KEY, {str(user_id): total_tiles_owned})
    except RedisError:
        logger.exception("leaderboard_update_failed", extra={"user_id": user_id})
