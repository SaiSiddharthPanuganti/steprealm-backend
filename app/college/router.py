from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.college.models import College
from app.college.schemas import JoinCollegeRequest
from app.database.session import get_db

router = APIRouter()


@router.post("/join")
def join_college(payload: JoinCollegeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    with db.begin():
        college = db.query(College).filter(College.join_code == payload.join_code).first()
        if not college:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid join code")

        user = db.query(User).filter(User.id == current_user.id).with_for_update().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        user.college_id = college.id

    return {
        "college_id": college.id,
        "college_name": college.name,
    }
