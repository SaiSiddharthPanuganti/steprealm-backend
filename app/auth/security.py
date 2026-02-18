from datetime import datetime, timedelta, timezone
import os

from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext


load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _get_jwt_settings() -> tuple[str, str]:
    secret_key = os.getenv("JWT_SECRET_KEY")
    if not secret_key:
        raise RuntimeError("JWT_SECRET_KEY environment variable is not set.")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    return secret_key, algorithm


def create_access_token(subject: str) -> str:
    secret_key, algorithm = _get_jwt_settings()
    expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=expire_minutes)
    payload = {
        "sub": subject,
        "type": "access",
        "iat": now,
        "nbf": now,
        "exp": expires_at,
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_access_token(token: str) -> dict:
    secret_key, algorithm = _get_jwt_settings()
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm],
            options={"require_exp": True, "require_sub": True, "require_iat": True, "require_nbf": True},
        )
    except JWTError as exc:
        raise ValueError("Invalid token") from exc

    if payload.get("type") != "access":
        raise ValueError("Invalid token")
    return payload
