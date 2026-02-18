import math

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.game.models import HexTile

CLAIM_COST = 20
WALK_CAPTURE_DISTANCE_METERS = 20.0
HEX_EDGE_LENGTH_METERS = 20.0
EARTH_RADIUS_METERS = 6378137.0
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


def user_owns_any_tile(db: Session, owner_id: int) -> bool:
    return db.query(HexTile.id).filter(HexTile.owner_id == owner_id).first() is not None


def mercator_from_lat_lng(latitude: float, longitude: float) -> tuple[float, float]:
    lat_rad = math.radians(max(min(latitude, 85.0), -85.0))
    lng_rad = math.radians(longitude)
    x = EARTH_RADIUS_METERS * lng_rad
    y = EARTH_RADIUS_METERS * math.log(math.tan((math.pi / 4.0) + (lat_rad / 2.0)))
    return x, y


def lat_lng_from_mercator(x: float, y: float) -> tuple[float, float]:
    longitude = math.degrees(x / EARTH_RADIUS_METERS)
    latitude = math.degrees((2.0 * math.atan(math.exp(y / EARTH_RADIUS_METERS))) - (math.pi / 2.0))
    return latitude, longitude


def axial_round(q: float, r: float) -> tuple[int, int]:
    x = q
    z = r
    y = -x - z

    rx = round(x)
    ry = round(y)
    rz = round(z)

    x_diff = abs(rx - x)
    y_diff = abs(ry - y)
    z_diff = abs(rz - z)

    if x_diff > y_diff and x_diff > z_diff:
        rx = -ry - rz
    elif y_diff > z_diff:
        ry = -rx - rz
    else:
        rz = -rx - ry

    return int(rx), int(rz)


def lat_lng_to_axial(latitude: float, longitude: float, edge_length_m: float = HEX_EDGE_LENGTH_METERS) -> tuple[int, int]:
    x, y = mercator_from_lat_lng(latitude, longitude)
    q = ((math.sqrt(3.0) / 3.0) * x - (1.0 / 3.0) * y) / edge_length_m
    r = ((2.0 / 3.0) * y) / edge_length_m
    return axial_round(q, r)


def axial_to_lat_lng(q: int, r: int, edge_length_m: float = HEX_EDGE_LENGTH_METERS) -> tuple[float, float]:
    x = edge_length_m * math.sqrt(3.0) * (q + (r / 2.0))
    y = edge_length_m * 1.5 * r
    return lat_lng_from_mercator(x, y)


def axial_to_boundary(q: int, r: int, edge_length_m: float = HEX_EDGE_LENGTH_METERS) -> list[tuple[float, float]]:
    center_x = edge_length_m * math.sqrt(3.0) * (q + (r / 2.0))
    center_y = edge_length_m * 1.5 * r

    points: list[tuple[float, float]] = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        x = center_x + edge_length_m * math.cos(angle)
        y = center_y + edge_length_m * math.sin(angle)
        lat, lng = lat_lng_from_mercator(x, y)
        points.append((lat, lng))
    return points


def axial_disk(center_q: int, center_r: int, radius: int) -> list[tuple[int, int]]:
    cells: list[tuple[int, int]] = []
    for dq in range(-radius, radius + 1):
        r_min = max(-radius, -dq - radius)
        r_max = min(radius, -dq + radius)
        for dr in range(r_min, r_max + 1):
            cells.append((center_q + dq, center_r + dr))
    return cells
