"""
Revision Service — Ghi vết lịch sử chỉnh sửa (Revision History) của câu hỏi & câu trả lời.
"""
from datetime import datetime, timezone
from bson import ObjectId

from app.core.database import revisions_col, users_col


async def record_revision(
    target_type: str,     # 'question' | 'answer'
    target_id: str,
    title: str | None,
    body: str,
    editor_id: str,
    comment: str = "Chỉnh sửa bài viết",
):
    """Lưu 1 bản snapshot lịch sử chỉnh sửa."""
    editor = await users_col.find_one({"_id": ObjectId(editor_id)}, {"username": 1, "displayName": 1})
    editor_name = editor.get("displayName", editor["username"]) if editor else "N/A"

    doc = {
        "targetType": target_type,
        "targetId": ObjectId(target_id),
        "title": title,
        "body": body,
        "editorId": ObjectId(editor_id),
        "editorName": editor_name,
        "comment": comment,
        "createdAt": datetime.now(timezone.utc),
    }
    await revisions_col.insert_one(doc)


async def get_revisions(target_type: str, target_id: str) -> list[dict]:
    """Lấy danh sách các bản chỉnh sửa từ cũ đến mới."""
    cursor = revisions_col.find(
        {"targetType": target_type, "targetId": ObjectId(target_id)}
    ).sort("createdAt", 1)

    return [
        {
            "id": str(r["_id"]),
            "title": r.get("title"),
            "body": r["body"],
            "editorId": str(r["editorId"]),
            "editorName": r["editorName"],
            "comment": r["comment"],
            "createdAt": r["createdAt"].isoformat(),
        }
        async for r in cursor
    ]
