import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database.session import get_db
from app.core.security import enforce_rate_limit
from app.mana.schemas import AddStepsRequest
from app.mana.service import apply_passive_regen, apply_step_bonus

router = APIRouter()
logger = logging.getLogger("steprealm.mana")


@router.post("/sync")
def sync_mana(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    logger.info("mana_sync_requested", extra={"user_id": current_user.id})
    try:
        user = db.query(User).filter(User.id == current_user.id).with_for_update().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        apply_passive_regen(user)
        db.commit()
    except Exception:
        db.rollback()
        raise

    logger.info("mana_sync_completed", extra={"user_id": user.id, "mana": user.mana})

    return {
        "mana": user.mana,
        "last_regen_time": user.last_regen_time,
    }


@router.post("/add-steps")
def add_steps(payload: AddStepsRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    enforce_rate_limit(scope="add_steps", subject_id=current_user.id, limit=6, window_seconds=60)
    try:
        user = db.query(User).filter(User.id == current_user.id).with_for_update().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        awarded_mana = apply_step_bonus(user, payload.step_delta)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "mana": user.mana,
        "daily_mana_earned": user.daily_mana_earned,
        "awarded_mana": awarded_mana,
    }
