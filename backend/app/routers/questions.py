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
        "isIndexed": False,  # sẽ được search module vector hóa ở Tuần 2 (chức năng B)
        "createdAt": now,
        "updatedAt": now,
    }
    result = await questions_col.insert_one(doc)
    doc["_id"] = result.inserted_id
    await sync_tags_on_create(doc["tags"])

    # Luồng index tự động (Phần 3/Ngày 13): index ngay bằng vocab hiện hành, đồng bộ.
    # Nếu chưa từng reindex_all() (chưa có vocab TF-IDF), hàm này tự bỏ qua an toàn -
    # isIndexed vẫn False cho tới lần reindex thủ công tiếp theo.
    await tfidf_service.index_single_question(doc["_id"], doc["title"], doc.get("body", ""))
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
    if payload.title is not None or payload.body is not None:
        # Tiêu đề hoặc nội dung đổi -> re-index ngay
        await tfidf_service.index_single_question(q["_id"], updated.get("title", ""), updated.get("body", ""))
    return {"question": await serialize_question(updated)}


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
