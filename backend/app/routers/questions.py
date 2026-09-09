from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import questions_col, answers_col, comments_col, votes_col
from app.core.security import get_current_user, require_reputation, check_owner_or_privilege
from app.core.privileges import PRIVILEGE
from app.models.question import QuestionCreateRequest, QuestionUpdateRequest
from app.services.tag_service import sync_tags_on_create, sync_tags_on_update, sync_tags_on_delete
from app.services.search import tfidf_service
from app.services import revision_service, badge_service
from app.services.reputation_service import adjust_reputation
from pydantic import BaseModel

from app.core.database import questions_col, answers_col, comments_col, votes_col, users_col

router = APIRouter(prefix="/api/questions", tags=["questions"])


async def serialize_question(q: dict, author_cache: Optional[dict] = None) -> dict:
    author_info = None
    author_id_str = str(q["authorId"])
    if author_cache and author_id_str in author_cache:
        author_info = author_cache[author_id_str]
    else:
        user = await users_col.find_one({"_id": q["authorId"]})
        if user:
            author_info = {
                "id": str(user["_id"]),
                "displayName": user.get("displayName", user.get("username", "User")),
                "reputation": user.get("reputation", 1),
            }
            if author_cache is not None:
                author_cache[author_id_str] = author_info

    return {
        "id": str(q["_id"]),
        "title": q["title"],
        "body": q["body"],
        "tags": q.get("tags", []),
        "authorId": author_id_str,
        "author": author_info,
        "viewCount": q.get("viewCount", 0),
        "voteScore": q.get("voteScore", 0),
        "answerCount": q.get("answerCount", 0),
        "acceptedAnswerId": str(q["acceptedAnswerId"]) if q.get("acceptedAnswerId") else None,
        "isIndexed": q.get("isIndexed", False),
        "isClosed": q.get("isClosed", False),
        "closeReason": q.get("closeReason"),
        "bounty": q.get("bounty", 0),
        "bountyExpiresAt": q["bountyExpiresAt"].isoformat() if q.get("bountyExpiresAt") else None,
        "createdAt": q["createdAt"].isoformat(),
        "updatedAt": q["updatedAt"].isoformat(),
    }


@router.get("")
async def list_questions(
    tag: Optional[str] = None,
    sort: str = Query("newest", regex="^(newest|votes|active|unanswered)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
):
    filt = {}
    if tag:
        filt["tags"] = tag.lower()

    if sort == "unanswered":
        filt["answerCount"] = 0
        sort_spec = [("createdAt", -1)]
    elif sort == "votes":
        sort_spec = [("voteScore", -1), ("createdAt", -1)]
    elif sort == "active":
        sort_spec = [("updatedAt", -1), ("createdAt", -1)]
    else:  # newest
        sort_spec = [("createdAt", -1)]

    total = await questions_col.count_documents(filt)
    cursor = (
        questions_col.find(filt)
        .sort(sort_spec)
        .skip((page - 1) * limit)
        .limit(limit)
    )
    docs = [q async for q in cursor]
    author_ids = list({q["authorId"] for q in docs})
    authors = {
        str(u["_id"]): {
            "id": str(u["_id"]),
            "displayName": u.get("displayName", u.get("username", "User")),
            "reputation": u.get("reputation", 1),
        }
        async for u in users_col.find({"_id": {"$in": author_ids}})
    }
    questions = [await serialize_question(q, author_cache=authors) for q in docs]
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    return {
        "questions": questions,
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": total_pages,
    }


@router.get("/{question_id}")
async def get_question(question_id: str):
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    q = await questions_col.find_one({"_id": ObjectId(question_id)})
    if not q:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")
    await questions_col.update_one({"_id": q["_id"]}, {"$inc": {"viewCount": 1}})
    q["viewCount"] = q.get("viewCount", 0) + 1
    # Đánh giá badge viewCount cho tác giả
    await badge_service.evaluate_user_badges(q["authorId"])
    return {"question": await serialize_question(q)}


@router.post("", status_code=201)
async def create_question(
    payload: QuestionCreateRequest,
    current_user: dict = Depends(require_reputation(PRIVILEGE["ASK_ANSWER"])),
):
    now = datetime.now(timezone.utc)
    doc = {
        "title": payload.title,
        "body": payload.body,
        "tags": [t.lower() for t in payload.tags],
        "authorId": current_user["_id"],
        "viewCount": 0,
        "voteScore": 0,
        "answerCount": 0,
        "acceptedAnswerId": None,
        "isIndexed": False,
        "isClosed": False,
        "closeReason": None,
        "bounty": 0,
        "bountyExpiresAt": None,
        "createdAt": now,
        "updatedAt": now,
    }
    result = await questions_col.insert_one(doc)
    doc["_id"] = result.inserted_id
    await sync_tags_on_create(doc["tags"])

    # Ghi bản revision v1 đầu tiên
    await revision_service.record_revision(
        target_type="question",
        target_id=str(doc["_id"]),
        title=doc["title"],
        body=doc["body"],
        editor_id=str(current_user["_id"]),
        comment="Tạo mới câu hỏi"
    )
    await badge_service.evaluate_user_badges(current_user["_id"])

    await tfidf_service.index_single_question(doc["_id"], doc["title"], doc.get("body", ""), doc["tags"] or [])
    updated = await questions_col.find_one({"_id": doc["_id"]})
    return {"question": await serialize_question(updated)}


@router.put("/{question_id}")
async def update_question(
    question_id: str,
    payload: QuestionUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    q = await questions_col.find_one({"_id": ObjectId(question_id)})
    if not q:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")

    # Chủ sở hữu HOẶC reputation >= EDIT_OTHERS_POST (500)
    check_owner_or_privilege(current_user, q["authorId"], PRIVILEGE["EDIT_OTHERS_POST"])

    update = {"updatedAt": datetime.now(timezone.utc)}
    if payload.title is not None:
        update["title"] = payload.title
        update["isIndexed"] = False  # tiêu đề đổi -> cần re-index vector
    if payload.body is not None:
        update["body"] = payload.body
    if payload.tags is not None:
        update["tags"] = [t.lower() for t in payload.tags]

    await questions_col.update_one({"_id": q["_id"]}, {"$set": update})
    if payload.tags is not None:
        await sync_tags_on_update(q.get("tags", []), update["tags"])
    updated = await questions_col.find_one({"_id": q["_id"]})

    # Ghi bản revision snapshot khi chỉnh sửa
    await revision_service.record_revision(
        target_type="question",
        target_id=str(q["_id"]),
        title=updated["title"],
        body=updated["body"],
        editor_id=str(current_user["_id"]),
        comment="Cập nhật câu hỏi"
    )

    if payload.title is not None or payload.body is not None or payload.tags is not None:
        await tfidf_service.index_single_question(q["_id"], updated.get("title", ""), updated.get("body", ""), updated.get("tags", []) or [])
    return {"question": await serialize_question(updated)}


class CloseQuestionRequest(BaseModel):
    reason: str


class BountyRequest(BaseModel):
    amount: int  # 50, 100, 200, 500


@router.get("/{question_id}/revisions")
async def list_question_revisions(question_id: str):
    """Lấy danh sách lịch sử chỉnh sửa (Revision History) của câu hỏi."""
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    revisions = await revision_service.get_revisions("question", question_id)
    return {"revisions": revisions}


@router.post("/{question_id}/close")
async def close_question(
    question_id: str,
    payload: CloseQuestionRequest,
    current_user: dict = Depends(get_current_user),
):
    """Đóng câu hỏi (chủ sở hữu hoặc admin hoặc rep >= 500). Không cho phép trả lời thêm."""
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    q = await questions_col.find_one({"_id": ObjectId(question_id)})
    if not q:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")

    check_owner_or_privilege(current_user, q["authorId"], PRIVILEGE["EDIT_OTHERS_POST"])
    await questions_col.update_one(
        {"_id": q["_id"]},
        {"$set": {"isClosed": True, "closeReason": payload.reason or "Trùng lặp hoặc không phù hợp"}}
    )
    return {"message": "Đã đóng câu hỏi"}


@router.post("/{question_id}/reopen")
async def reopen_question(question_id: str, current_user: dict = Depends(get_current_user)):
    """Mở lại câu hỏi đã đóng."""
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    q = await questions_col.find_one({"_id": ObjectId(question_id)})
    if not q:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")

    check_owner_or_privilege(current_user, q["authorId"], PRIVILEGE["EDIT_OTHERS_POST"])
    await questions_col.update_one({"_id": q["_id"]}, {"$set": {"isClosed": False, "closeReason": None}})
    return {"message": "Đã mở lại câu hỏi"}


@router.post("/{question_id}/bounty")
async def set_bounty(
    question_id: str,
    payload: BountyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Đặt cọc thưởng reputation (Bounty: +50, +100, +200, +500). Trừ rep của người đặt cọc."""
    if payload.amount not in [50, 100, 200, 500]:
        raise HTTPException(status_code=400, detail="Mức bounty phải là 50, 100, 200 hoặc 500")

    if current_user.get("reputation", 1) < payload.amount:
        raise HTTPException(status_code=400, detail=f"Bạn cần ít nhất {payload.amount} reputation để treo thưởng")

    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    q = await questions_col.find_one({"_id": ObjectId(question_id)})
    if not q:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")

    if q.get("bounty", 0) > 0:
        raise HTTPException(status_code=400, detail="Câu hỏi này đã có bounty đang mở")

    from datetime import timedelta
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    # Trừ rep người đặt cọc
    await adjust_reputation(str(current_user["_id"]), -payload.amount, "bounty_created", question_id)
    await questions_col.update_one(
        {"_id": q["_id"]},
        {"$set": {"bounty": payload.amount, "bountyExpiresAt": expires_at}}
    )
    return {"message": f"Đã treo thưởng +{payload.amount} reputation thành công"}


@router.delete("/{question_id}")
async def delete_question(question_id: str, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    q = await questions_col.find_one({"_id": ObjectId(question_id)})
    if not q:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")

    # Chủ sở hữu HOẶC reputation >= DELETE_OTHERS_QUESTION (2000)
    check_owner_or_privilege(current_user, q["authorId"], PRIVILEGE["DELETE_OTHERS_QUESTION"])

    # Cascade: xóa toàn bộ answer/comment/vote liên quan để tránh dữ liệu mồ côi
    answer_ids = [a["_id"] async for a in answers_col.find({"questionId": q["_id"]}, {"_id": 1})]
    await answers_col.delete_many({"questionId": q["_id"]})
    await comments_col.delete_many({"targetType": "question", "targetId": q["_id"]})
    if answer_ids:
        await comments_col.delete_many({"targetType": "answer", "targetId": {"$in": answer_ids}})
        await votes_col.delete_many({"targetType": "answer", "targetId": {"$in": answer_ids}})
    await votes_col.delete_many({"targetType": "question", "targetId": q["_id"]})
    await sync_tags_on_delete(q.get("tags", []))

    await questions_col.delete_one({"_id": q["_id"]})

    # Dọn vector chỉ mục tương ứng (không để "mồ côi" trong collection vector)
    await tfidf_service.remove_question(q["_id"])

    return {"message": "Đã xóa câu hỏi"}
