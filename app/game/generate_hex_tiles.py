from app.database.session import SessionLocal
from app.game.models import HexTile

TARGET_TILE_COUNT = 800
BASE_RADIUS = 16


def axial_hexes_within_radius(radius: int) -> list[tuple[int, int]]:
    coords: list[tuple[int, int]] = []
    for q in range(-radius, radius + 1):
        r_min = max(-radius, -q - radius)
        r_max = min(radius, -q + radius)
        for r in range(r_min, r_max + 1):
            coords.append((q, r))
    return coords


def hex_distance(q: int, r: int) -> int:
    s = -q - r
    return max(abs(q), abs(r), abs(s))


def generate_target_coords() -> list[tuple[int, int]]:
    coords = axial_hexes_within_radius(BASE_RADIUS)
    coords.sort(key=lambda c: (hex_distance(c[0], c[1]), abs(c[0]), abs(c[1]), c[0], c[1]))
    return coords[:TARGET_TILE_COUNT]


def main() -> None:
    db = SessionLocal()
    try:
        existing = db.query(HexTile.id).limit(1).first()
        if existing is not None:
            print("Hex tiles already exist. Skipping.")
            return

        coords = generate_target_coords()
        tiles = [HexTile(q=q, r=r) for q, r in coords]

        db.bulk_save_objects(tiles)
        db.commit()
        print(f"Inserted {len(tiles)} hex tiles.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
