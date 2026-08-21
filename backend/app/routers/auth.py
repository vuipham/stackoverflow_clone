from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import users_col
from app.core.security import create_access_token, get_current_user
from app.core.password import hash_password, verify_password
from app.models.user import UserRegisterRequest, UserLoginRequest, UserPublic, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


def to_public_user(user: dict) -> UserPublic:
    return UserPublic(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        displayName=user["displayName"],
        reputation=user.get("reputation", 1),
        isAdmin=user.get("isAdmin", False),
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: UserRegisterRequest):
    existed = await users_col.find_one({"$or": [{"username": payload.username}, {"email": payload.email}]})
    if existed:
        raise HTTPException(status_code=409, detail="Username hoặc email đã tồn tại")

    password_hash = hash_password(payload.password)
    doc = {
        "username": payload.username,
        "email": payload.email,
        "passwordHash": password_hash,
        "displayName": payload.displayName or payload.username,
        "isAdmin": False,
        "isBanned": False,
        "reputation": 1,  # mặc định 1, đúng thực tế Stack Overflow
        "reputationLog": [],
    }
    result = await users_col.insert_one(doc)
    doc["_id"] = result.inserted_id

    token = create_access_token(str(doc["_id"]))
    return TokenResponse(token=token, user=to_public_user(doc))


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest):
    user = await users_col.find_one({"username": payload.username})
    if not user:
        raise HTTPException(status_code=401, detail="Sai username hoặc password")
    if user.get("isBanned"):
        raise HTTPException(status_code=403, detail="Tài khoản đã bị khóa")
    if not verify_password(payload.password, user["passwordHash"]):
        raise HTTPException(status_code=401, detail="Sai username hoặc password")

    token = create_access_token(str(user["_id"]))
    return TokenResponse(token=token, user=to_public_user(user))


@router.get("/me", response_model=UserPublic)
async def me(current_user: dict = Depends(get_current_user)):
    return to_public_user(current_user)
