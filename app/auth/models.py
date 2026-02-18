from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("mana >= 0", name="ck_users_mana_non_negative"),
        CheckConstraint("mana <= 200", name="ck_users_mana_max_cap"),
        CheckConstraint("daily_mana_earned >= 0", name="ck_users_daily_mana_non_negative"),
        CheckConstraint("daily_mana_earned <= 200", name="ck_users_daily_mana_max_cap"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    mana: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_regen_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    daily_mana_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    college_id: Mapped[int | None] = mapped_column(ForeignKey("colleges.id"), nullable=True, index=True)
