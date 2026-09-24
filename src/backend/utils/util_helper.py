from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional
import os
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from src.backend.config.db import get_db

# Resolve .env relative to this file (backend root)
_env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=_env_path)

# Password hashing context.
# bcrypt__truncate_error=False: suppress passlib's own 72-byte guard — we
# handle truncation ourselves at the byte level in _truncate_password().
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=False,
)

# JWT configuration from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def _truncate_password(password: str) -> bytes:
    """
    Encode the password to UTF-8 bytes and truncate to 72 bytes.
    Must be done at byte level — a [:72] character slice can still exceed
    72 bytes when the password contains multi-byte Unicode characters.
    """
    return password.encode("utf-8")[:72]


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    try:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        raise ValueError("Error occurred while creating access token") from e


def verify_token(token: str = Depends(oauth2_scheme)) -> dict:
    """Decode and validate a JWT token (FastAPI dependency)."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def decode_access_token(token: str) -> Optional[dict]:
    """Decode a JWT token, returning None on any failure."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return pwd_context.verify(_truncate_password(plain_password), hashed_password)


def hash_password(password: str) -> str:
    """Hash a password with bcrypt, safely truncated to 72 bytes."""
    return pwd_context.hash(_truncate_password(password))


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """FastAPI dependency that returns the current authenticated user's payload."""
    return verify_token(token)


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """FastAPI dependency that raises 403 if user is not admin."""
    if current_user.get("designation") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def get_user_from_db(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns the full User ORM object from the database."""
    from src.backend.models.user_model import User
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user