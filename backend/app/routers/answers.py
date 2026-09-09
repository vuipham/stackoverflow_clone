from datetime import datetime, timezone
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import answers_col, questions_col, comments_col, votes_col
from app.core.security import get_current_user, require_reputation, check_owner_or_privilege
from app.core.privileges import PRIVILEGE, REPUTATION_DELTA
from app.models.answer import AnswerCreateRequest, AnswerUpdateRequest
from app.services.reputation_service import adjust_reputation
from app.services import notification_service

# Router lồng trong /api/questions/{question_id}/answers để tạo/liệt kê,
# và /api/answers/{answer_id} để sửa/xóa/accept - gộp chung 1 router cho gọn.
router = APIRouter(tags=["answers"])


from app.core.database import answers_col, questions_col, comments_col, votes_col, users_col


async def serialize_answer(a: dict, author_cache: dict = None) -> dict:
    author_info = None
    author_id_str = str(a["authorId"])
    if author_cache and author_id_str in author_cache:
        author_info = author_cache[author_id_str]
    else:
        user = await users_col.find_one({"_id": a["authorId"]})
        if user:
            author_info = {
                "id": str(user["_id"]),
                "displayName": user.get("displayName", user.get("username", "User")),
                "reputation": user.get("reputation", 1),
            }
            if author_cache is not None:
                author_cache[author_id_str] = author_info

    return {
        "id": str(a["_id"]),
        "questionId": str(a["questionId"]),
        "authorId": author_id_str,
        "author": author_info,
        "body": a["body"],
        "voteScore": a.get("voteScore", 0),
        "isAccepted": a.get("isAccepted", False),
        "createdAt": a["createdAt"].isoformat(),
    }


async def _get_question_or_404(question_id: str) -> dict:
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=400, detail="ID câu hỏi không hợp lệ")
    q = await questions_col.find_one({"_id": ObjectId(question_id)})
    if not q:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")
    return q


@router.get("/api/questions/{question_id}/answers")
async def list_answers(question_id: str):
    await _get_question_or_404(question_id)
    cursor = answers_col.find({"questionId": ObjectId(question_id)}).sort(
        [("isAccepted", -1), ("voteScore", -1), ("createdAt", 1)]
    )
    docs = [a async for a in cursor]
    author_ids = list({a["authorId"] for a in docs})
    authors = {
        str(u["_id"]): {
            "id": str(u["_id"]),
            "displayName": u.get("displayName", u.get("username", "User")),
            "reputation": u.get("reputation", 1),
        }
        async for u in users_col.find({"_id": {"$in": author_ids}})
    }
    answers = [await serialize_answer(a, author_cache=authors) for a in docs]
    return {"answers": answers}


@router.post("/api/questions/{question_id}/answers", status_code=201)
async def create_answer(
    question_id: str,
    payload: AnswerCreateRequest,
    current_user: dict = Depends(require_reputation(PRIVILEGE["ASK_ANSWER"])),
):
    q = await _get_question_or_404(question_id)
    if q.get("isClosed"):
        raise HTTPException(status_code=400, detail="Câu hỏi này đã bị đóng, không thể trả lời thêm")

    now = datetime.now(timezone.utc)
    doc = {
        "questionId": q["_id"],
        "authorId": current_user["_id"],
        "body": payload.body,
        "voteScore": 0,
        "isAccepted": False,
        "createdAt": now,
    }
    result = await answers_col.insert_one(doc)
    doc["_id"] = result.inserted_id

    await questions_col.update_one({"_id": q["_id"]}, {"$inc": {"answerCount": 1}})
    from app.services import badge_service
    await badge_service.evaluate_user_badges(current_user["_id"])

    # Thông báo cho tác giả câu hỏi (nếu không phải chính mình)
    if str(q["authorId"]) != str(current_user["_id"]):
        await notification_service.push(
            recipient_id=q["authorId"],
            event_type="new_answer",
            actor_name=current_user.get("displayName", current_user["username"]),
            question_id=str(q["_id"]),
            question_title=q["title"],
            ref_id=str(doc["_id"]),
        )

    return {"answer": await serialize_answer(doc)}


@router.put("/api/answers/{answer_id}")
async def update_answer(answer_id: str, payload: AnswerUpdateRequest, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(answer_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    a = await answers_col.find_one({"_id": ObjectId(answer_id)})
    if not a:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu trả lời")

    # Chủ sở hữu HOẶC reputation >= EDIT_OTHERS_POST (500) - dùng chung ngưỡng với sửa question
    check_owner_or_privilege(current_user, a["authorId"], PRIVILEGE["EDIT_OTHERS_POST"])

    await answers_col.update_one({"_id": a["_id"]}, {"$set": {"body": payload.body}})
    updated = await answers_col.find_one({"_id": a["_id"]})
    return {"answer": await serialize_answer(updated)}


@router.delete("/api/answers/{answer_id}")
async def delete_answer(answer_id: str, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(answer_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    a = await answers_col.find_one({"_id": ObjectId(answer_id)})
    if not a:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu trả lời")

    # Dùng chung ngưỡng EDIT_OTHERS_POST (500) cho quyền xóa bài người khác ở mức answer
    # (đề tài không định nghĩa ngưỡng riêng cho xóa answer của người khác)
    check_owner_or_privilege(current_user, a["authorId"], PRIVILEGE["EDIT_OTHERS_POST"])

    await comments_col.delete_many({"targetType": "answer", "targetId": a["_id"]})
    await votes_col.delete_many({"targetType": "answer", "targetId": a["_id"]})
    await answers_col.delete_one({"_id": a["_id"]})
    await questions_col.update_one({"_id": a["questionId"]}, {"$inc": {"answerCount": -1}})
    if a.get("isAccepted"):
        await questions_col.update_one({"_id": a["questionId"]}, {"$set": {"acceptedAnswerId": None}})

    return {"message": "Đã xóa câu trả lời"}


@router.post("/api/answers/{answer_id}/accept")
async def accept_answer(answer_id: str, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(answer_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    a = await answers_col.find_one({"_id": ObjectId(answer_id)})
    if not a:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu trả lời")
    q = await questions_col.find_one({"_id": a["questionId"]})
    if not q:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")

    # Chỉ tác giả câu hỏi (hoặc Admin) mới được chấp nhận câu trả lời - đúng thực tế Stack Overflow
    is_owner = str(q["authorId"]) == str(current_user["_id"])
    if not is_owner and not current_user.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Chỉ tác giả câu hỏi mới được chấp nhận câu trả lời")

    if q.get("acceptedAnswerId"):
        await answers_col.update_one({"_id": q["acceptedAnswerId"]}, {"$set": {"isAccepted": False}})

    await answers_col.update_one({"_id": a["_id"]}, {"$set": {"isAccepted": True}})
    
    bounty_amount = q.get("bounty", 0)
    bounty_update = {"acceptedAnswerId": a["_id"]}
    if bounty_amount > 0:
        # Chuyển bounty rep cho tác giả câu trả lời
        await adjust_reputation(str(a["authorId"]), bounty_amount, "bounty_won", str(q["_id"]))
        bounty_update["bounty"] = 0
        bounty_update["bountyExpiresAt"] = None

    await questions_col.update_one({"_id": q["_id"]}, {"$set": bounty_update})
    await adjust_reputation(str(a["authorId"]), REPUTATION_DELTA["ANSWER_ACCEPTED"], "answer_accepted", str(a["_id"]))

    from app.services import badge_service
    await badge_service.evaluate_user_badges(a["authorId"])
    await badge_service.evaluate_user_badges(q["authorId"])

    # Thông báo cho tác giả câu trả lời (nếu không phải chính mình)
    if str(a["authorId"]) != str(current_user["_id"]):
        await notification_service.push(
            recipient_id=a["authorId"],
            event_type="answer_accepted",
            actor_name=current_user.get("displayName", current_user["username"]),
            question_id=str(q["_id"]),
            question_title=q["title"],
            ref_id=str(a["_id"]),
        )

    updated = await answers_col.find_one({"_id": a["_id"]})
    return {"answer": await serialize_answer(updated)}
