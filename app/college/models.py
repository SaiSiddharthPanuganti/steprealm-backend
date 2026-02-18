from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class College(Base):
    __tablename__ = "colleges"
    __table_args__ = (
        CheckConstraint("total_tiles >= 0", name="ck_colleges_total_tiles_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    join_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    total_tiles: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
