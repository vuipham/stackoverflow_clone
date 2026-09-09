"""
Router: Bookmark — lưu/bỏ lưu câu hỏi, xem danh sách bookmark của mình.

Endpoints:
  POST   /api/bookmarks             — toggle bookmark (thêm nếu chưa có, xóa nếu đã có)
  GET    /api/bookmarks/me          — danh sách câu hỏi đã bookmark (có phân trang)
  GET    /api/bookmarks/me/{qid}    — kiểm tra 1 câu hỏi đã bookmark chưa
"""
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.database import bookmarks_col, questions_col
from app.core.security import get_current_user

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])


class BookmarkRequest(BaseModel):
    questionId: str


def _q_brief(q: dict) -> dict:
    return {
        "id": str(q["_id"]),
        "title": q["title"],
        "tags": q.get("tags", []),
        "voteScore": q.get("voteScore", 0),
        "answerCount": q.get("answerCount", 0),
        "acceptedAnswerId": str(q["acceptedAnswerId"]) if q.get("acceptedAnswerId") else None,
        "createdAt": q["createdAt"].isoformat(),
    }


@router.post("")
async def toggle_bookmark(payload: BookmarkRequest, current_user: dict = Depends(get_current_user)):
    """Toggle bookmark: thêm nếu chưa có, xóa nếu đã có. Trả về trạng thái sau toggle."""
    if not ObjectId.is_valid(payload.questionId):
        raise HTTPException(status_code=400, detail="questionId không hợp lệ")

    q = await questions_col.find_one({"_id": ObjectId(payload.questionId)}, {"_id": 1})
    if not q:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")

    existing = await bookmarks_col.find_one(
        {"userId": current_user["_id"], "questionId": ObjectId(payload.questionId)}
    )

    if existing:
        # Đã bookmark → bỏ bookmark
        await bookmarks_col.delete_one({"_id": existing["_id"]})
        return {"bookmarked": False, "message": "Đã bỏ bookmark"}
    else:
        # Chưa bookmark → thêm
        try:
            await bookmarks_col.insert_one(
                {
                    "userId": current_user["_id"],
                    "questionId": ObjectId(payload.questionId),
                    "createdAt": datetime.now(timezone.utc),
                }
            )
        except DuplicateKeyError:
            pass  # race condition, vẫn trả về bookmarked=True
        return {"bookmarked": True, "message": "Đã bookmark câu hỏi"}


@router.get("/me/{question_id}")
async def check_bookmark(question_id: str, current_user: dict = Depends(get_current_user)):
    """Kiểm tra câu hỏi có đang được bookmark không — dùng khi render trang chi tiết."""
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    exists = await bookmarks_col.find_one(
        {"userId": current_user["_id"], "questionId": ObjectId(question_id)}
    )
    return {"bookmarked": bool(exists)}


@router.get("/me")
async def list_my_bookmarks(
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    """Danh sách câu hỏi đã bookmark, mới nhất lên đầu, có phân trang."""
    total = await bookmarks_col.count_documents({"userId": current_user["_id"]})
    cursor = (
        bookmarks_col.find({"userId": current_user["_id"]})
        .sort("createdAt", -1)
        .skip((page - 1) * limit)
        .limit(limit)
    )
    bms = [b async for b in cursor]
    q_ids = [b["questionId"] for b in bms]
    q_map = {
        str(q["_id"]): q
        async for q in questions_col.find(
            {"_id": {"$in": q_ids}},
            {"title": 1, "tags": 1, "voteScore": 1, "answerCount": 1, "acceptedAnswerId": 1, "createdAt": 1},
        )
    }
    questions = [_q_brief(q_map[str(b["questionId"])]) for b in bms if str(b["questionId"]) in q_map]
    return {
        "questions": questions,
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": max(1, (total + limit - 1) // limit),
    }
