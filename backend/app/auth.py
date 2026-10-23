"""Auth utilities: JWT creation/validation and password hashing."""
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.database import get_db

bearer_scheme = HTTPBearer(auto_error=True)


# ── Password hashing ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload.get("sub")
    except JWTError:
        return None


# ── Dependency ────────────────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """FastAPI dependency that validates the JWT and returns the user document."""
    token = credentials.credentials
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    from bson import ObjectId, errors
    db = get_db()
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except errors.InvalidId:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token credentials",
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user
