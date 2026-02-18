from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.game.models import HexTile

CLAIM_COST = 20
AXIAL_DIRECTIONS = [
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
]


def has_adjacent_owned_tile(db: Session, owner_id: int, q: int, r: int) -> bool:
    neighbors = [(q + dq, r + dr) for dq, dr in AXIAL_DIRECTIONS]

    adjacency_filters = [and_(HexTile.q == nq, HexTile.r == nr) for nq, nr in neighbors]
    if not adjacency_filters:
        return False

    existing = (
        db.query(HexTile.id)
        .filter(HexTile.owner_id == owner_id)
        .filter(or_(*adjacency_filters))
        .first()
    )
    return existing is not None
