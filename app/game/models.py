from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class HexTile(Base):
    __tablename__ = "hex_tiles"
    __table_args__ = (
        UniqueConstraint("q", "r", name="uq_hex_tiles_q_r"),
        Index("ix_hex_tiles_q_r", "q", "r"),
        CheckConstraint("defense_level >= 1", name="ck_hex_tiles_defense_level_min"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    q: Mapped[int] = mapped_column(Integer, nullable=False)
    r: Mapped[int] = mapped_column(Integer, nullable=False)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    defense_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
