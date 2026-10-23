"""Authentication endpoints: signup, login, logout, me."""
from fastapi import APIRouter, HTTPException, status
from bson import ObjectId
from datetime import datetime, timezone

from app.database import get_db
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.schemas import SignupRequest, LoginRequest, AuthResponse, UserOut
from fastapi import Depends

router = APIRouter()


def _user_to_out(user: dict) -> UserOut:
    return UserOut(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"],
    )


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupRequest):
    db = get_db()
    email = body.email.lower().strip()

    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    doc = {
        "name": body.name.strip(),
        "email": email,
        "password_hash": hash_password(body.password),
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(doc)
    doc["_id"] = result.inserted_id

    token = create_access_token(str(result.inserted_id))
    return AuthResponse(access_token=token, user=_user_to_out(doc))


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    db = get_db()
    email = body.email.lower().strip()
    user = await db.users.find_one({"email": email})

    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_access_token(str(user["_id"]))
    return AuthResponse(access_token=token, user=_user_to_out(user))


@router.post("/logout")
async def logout():
    # JWT is stateless; client must discard the token
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user)):
    return _user_to_out(current_user)
