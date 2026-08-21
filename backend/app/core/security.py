from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.database import users_col

security = HTTPBearer()


def create_access_token(user_id: str) -> str:
    payload = {
        "userId": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expires_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Giải mã JWT, tra lại user MỚI NHẤT từ DB (không tin số reputation cũ trong token,
    vì reputation thay đổi liên tục theo vote).
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn")

    user = await users_col.find_one({"_id": ObjectId(payload["userId"])})
    if not user:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")
    if user.get("isBanned"):
        raise HTTPException(status_code=403, detail="Tài khoản đã bị khóa")

    return user  # dict Mongo đầy đủ, luôn có reputation mới nhất


def require_reputation(threshold: int):
    """Yêu cầu reputation >= threshold. Dùng cho hành động luôn cần đủ điểm (vd. upvote, downvote)."""

    async def checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("reputation", 0) < threshold:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": f"Cần tối thiểu {threshold} điểm reputation để thực hiện hành động này",
                    "currentReputation": current_user.get("reputation", 0),
                },
            )
        return current_user

    return checker


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Chỉ Admin (isAdmin=true) mới được đi qua - tách biệt hoàn toàn khỏi cơ chế reputation."""
    if not current_user.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Chỉ Admin mới được thực hiện hành động này")
    return current_user


def check_owner_or_privilege(current_user: dict, owner_id, threshold: int):
    """
    Cho phép nếu là chủ sở hữu tài nguyên HOẶC có đủ reputation.
    Dùng trực tiếp trong route (không phải Depends) vì cần owner_id lấy từ DB trước.
    """
    is_owner = str(owner_id) == str(current_user["_id"])
    has_privilege = current_user.get("reputation", 0) >= threshold
    if not is_owner and not has_privilege:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": f"Chỉ chủ sở hữu hoặc user có từ {threshold} điểm reputation mới thực hiện được",
                "currentReputation": current_user.get("reputation", 0),
            },
        )
