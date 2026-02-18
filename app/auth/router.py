import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.auth.security import create_access_token, hash_password, verify_password
from app.database.session import get_db

router = APIRouter()
logger = logging.getLogger("steprealm.auth")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    try:
        with db.begin():
            db.add(user)
            db.flush()
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        logger.warning("login_failed")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(str(user.id))
    logger.info("login_success", extra={"user_id": user.id})
    return TokenResponse(access_token=token)
