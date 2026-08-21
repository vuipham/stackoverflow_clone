from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import questions_col, answers_col, comments_col, votes_col
from app.core.security import get_current_user, require_reputation, check_owner_or_privilege
from app.core.privileges import PRIVILEGE
from app.models.question import QuestionCreateRequest, QuestionUpdateRequest
from app.services.tag_service import sync_tags_on_create, sync_tags_on_update, sync_tags_on_delete
from app.services.search import tfidf_service, sbert_service

router = APIRouter(prefix="/api/questions", tags=["questions"])


def serialize_question(q: dict) -> dict:
    return {
        "id": str(q["_id"]),
        "title": q["title"],
        "body": q["body"],
        "tags": q.get("tags", []),
        "authorId": str(q["authorId"]),
        "viewCount": q.get("viewCount", 0),
        "voteScore": q.get("voteScore", 0),
        "answerCount": q.get("answerCount", 0),
        "acceptedAnswerId": str(q["acceptedAnswerId"]) if q.get("acceptedAnswerId") else None,
        "isIndexed": q.get("isIndexed", False),
        "createdAt": q["createdAt"].isoformat(),
        "updatedAt": q["updatedAt"].isoformat(),
    }


@router.get("")
async def list_questions(tag: Optional[str] = None, page: int = Query(1, ge=1), limit: int = Query(20, le=100)):
    filt = {"tags": tag.lower()} if tag else {}
    cursor = questions_col.find(filt).sort("createdAt", -1).skip((page - 1) * limit).limit(limit)
    questions = [serialize_question(q) async for q in cursor]
    return {"questions": questions}


@router.get("/{question_id}")
async def get_question(question_id: str):
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    q = await questions_col.find_one({"_id": ObjectId(question_id)})
    if not q:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")
    await questions_col.update_one({"_id": q["_id"]}, {"$inc": {"viewCount": 1}})
    q["viewCount"] = q.get("viewCount", 0) + 1
    return {"question": serialize_question(q)}


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
        "isIndexed": False,  # sẽ được search module vector hóa ở Tuần 2 (chức năng B)
        "createdAt": now,
        "updatedAt": now,
    }
    result = await questions_col.insert_one(doc)
    doc["_id"] = result.inserted_id
    await sync_tags_on_create(doc["tags"])

    # Luồng index tự động (Phần 3/Ngày 13): index ngay bằng vocab/model hiện hành, đồng bộ.
    # Nếu chưa từng reindex_all() (chưa có vocab TF-IDF / model SBERT chưa sẵn sàng), các hàm
    # này tự bỏ qua an toàn - isIndexed vẫn False cho tới lần reindex thủ công tiếp theo.
    await tfidf_service.index_single_question(doc["_id"], doc["title"])
    await sbert_service.index_single_question(doc["_id"], doc["title"])
    updated = await questions_col.find_one({"_id": doc["_id"]})
    return {"question": serialize_question(updated)}


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
    if payload.title is not None:
        # Tiêu đề đổi -> re-index ngay để search luôn phản ánh dữ liệu mới nhất
        await tfidf_service.index_single_question(q["_id"], payload.title)
        await sbert_service.index_single_question(q["_id"], payload.title)
    updated = await questions_col.find_one({"_id": q["_id"]})
    return {"question": serialize_question(updated)}


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

    # Dọn vector chỉ mục tương ứng (không để "mồ côi" trong 2 collection vector)
    await tfidf_service.remove_question(q["_id"])
    await sbert_service.remove_question(q["_id"])

    return {"message": "Đã xóa câu hỏi"}
