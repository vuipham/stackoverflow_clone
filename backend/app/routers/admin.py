from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import users_col
from app.core.security import require_admin
from app.models.admin import AdminAdjustReputationRequest, AdminBanRequest
from app.services.reputation_service import adjust_reputation

router = APIRouter(prefix="/api/admin", tags=["admin"])


def serialize_user(u: dict) -> dict:
    return {
        "id": str(u["_id"]),
        "username": u["username"],
        "email": u["email"],
        "displayName": u["displayName"],
        "reputation": u.get("reputation", 1),
        "isAdmin": u.get("isAdmin", False),
        "isBanned": u.get("isBanned", False),
    }


@router.get("/users")
async def list_users(
    q: str | None = Query(None, description="Lọc theo username (chứa chuỗi)"),
    _admin: dict = Depends(require_admin),
):
    filt = {"username": {"$regex": q, "$options": "i"}} if q else {}
    cursor = users_col.find(filt).sort("reputation", -1)
    users = [serialize_user(u) async for u in cursor]
    return {"users": users}


@router.patch("/users/{user_id}/ban")
async def ban_user(user_id: str, payload: AdminBanRequest, _admin: dict = Depends(require_admin)):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    result = await users_col.update_one({"_id": ObjectId(user_id)}, {"$set": {"isBanned": payload.isBanned}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy user")
    updated = await users_col.find_one({"_id": ObjectId(user_id)})
    return {"user": serialize_user(updated)}


@router.patch("/users/{user_id}/reputation")
async def adjust_user_reputation(
    user_id: str, payload: AdminAdjustReputationRequest, _admin: dict = Depends(require_admin)
):
    """Admin chỉnh tay reputation - dùng chung service adjust_reputation() để có log giải trình."""
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    existed = await users_col.find_one({"_id": ObjectId(user_id)})
    if not existed:
        raise HTTPException(status_code=404, detail="Không tìm thấy user")
    updated = await adjust_reputation(user_id, payload.delta, payload.reason)
    return {"user": serialize_user(updated)}
