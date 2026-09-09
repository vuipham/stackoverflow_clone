"""
Router: Notifications — xem, đánh dấu đã đọc, đếm unread.

Endpoints:
  GET   /api/notifications          — danh sách thông báo (mới nhất trước), phân trang
  GET   /api/notifications/unread-count  — số thông báo chưa đọc (dùng cho badge)
  PATCH /api/notifications/read-all — đánh dấu tất cả đã đọc
  PATCH /api/notifications/{id}/read — đánh dấu 1 thông báo đã đọc
"""
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import notifications_col
from app.core.security import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def _serialize(n: dict) -> dict:
    return {
        "id": str(n["_id"]),
        "eventType": n["eventType"],
        "actorName": n["actorName"],
        "questionId": n["questionId"],
        "questionTitle": n["questionTitle"],
        "refId": n.get("refId"),
        "isRead": n["isRead"],
        "createdAt": n["createdAt"].isoformat(),
    }


@router.get("")
async def list_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    total = await notifications_col.count_documents({"recipientId": current_user["_id"]})
    cursor = (
        notifications_col.find({"recipientId": current_user["_id"]})
        .sort("createdAt", -1)
        .skip((page - 1) * limit)
        .limit(limit)
    )
    items = [_serialize(n) async for n in cursor]
    return {
        "notifications": items,
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": max(1, (total + limit - 1) // limit),
    }


@router.get("/unread-count")
async def unread_count(current_user: dict = Depends(get_current_user)):
    """Trả về số thông báo chưa đọc — dùng để hiển thị badge số đỏ trên icon chuông."""
    count = await notifications_col.count_documents(
        {"recipientId": current_user["_id"], "isRead": False}
    )
    return {"unreadCount": count}


@router.patch("/read-all")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    """Đánh dấu tất cả thông báo của user là đã đọc."""
    result = await notifications_col.update_many(
        {"recipientId": current_user["_id"], "isRead": False},
        {"$set": {"isRead": True}},
    )
    return {"markedRead": result.modified_count}


@router.patch("/{notification_id}/read")
async def mark_one_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Đánh dấu 1 thông báo là đã đọc."""
    if not ObjectId.is_valid(notification_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    result = await notifications_col.update_one(
        {"_id": ObjectId(notification_id), "recipientId": current_user["_id"]},
        {"$set": {"isRead": True}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông báo")
    return {"ok": True}
