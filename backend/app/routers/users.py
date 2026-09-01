from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import users_col, questions_col, answers_col
from app.core.security import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


def serialize_rep_log(entry: dict) -> dict:
    return {
        "delta": entry.get("delta", 0),
        "reason": entry.get("reason", ""),
        "refId": entry.get("refId"),
        "at": entry["at"].isoformat() if entry.get("at") else None,
    }


def serialize_question_brief(q: dict) -> dict:
    return {
        "id": str(q["_id"]),
        "title": q["title"],
        "tags": q.get("tags", []),
        "voteScore": q.get("voteScore", 0),
        "answerCount": q.get("answerCount", 0),
        "createdAt": q["createdAt"].isoformat(),
    }


def serialize_answer_brief(a: dict) -> dict:
    return {
        "id": str(a["_id"]),
        "questionId": str(a["questionId"]),
        "body": a["body"][:200] + ("..." if len(a["body"]) > 200 else ""),
        "voteScore": a.get("voteScore", 0),
        "isAccepted": a.get("isAccepted", False),
        "createdAt": a["createdAt"].isoformat(),
    }


@router.get("/{user_id}")
async def get_user_profile(user_id: str):
    """Hồ sơ công khai của một user — UC009."""
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    user = await users_col.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    questions_cursor = questions_col.find({"authorId": user["_id"]}).sort("createdAt", -1).limit(50)
    questions = [serialize_question_brief(q) async for q in questions_cursor]

    answers_cursor = answers_col.find({"authorId": user["_id"]}).sort("createdAt", -1).limit(50)
    answers = [serialize_answer_brief(a) async for a in answers_cursor]

    # reputationLog chỉ trả về 30 bản ghi gần nhất (tránh payload quá lớn)
    rep_log = [serialize_rep_log(e) for e in (user.get("reputationLog") or [])[-30:]]
    rep_log.reverse()  # mới nhất lên đầu

    return {
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "displayName": user["displayName"],
            "reputation": user.get("reputation", 1),
            "isAdmin": user.get("isAdmin", False),
            "isBanned": user.get("isBanned", False),
        },
        "reputationLog": rep_log,
        "questions": questions,
        "answers": answers,
    }


@router.get("/me/profile")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Hồ sơ cá nhân của chính mình — UC009, bao gồm email."""
    questions_cursor = questions_col.find({"authorId": current_user["_id"]}).sort("createdAt", -1).limit(50)
    questions = [serialize_question_brief(q) async for q in questions_cursor]

    answers_cursor = answers_col.find({"authorId": current_user["_id"]}).sort("createdAt", -1).limit(50)
    answers = [serialize_answer_brief(a) async for a in answers_cursor]

    rep_log = [serialize_rep_log(e) for e in (current_user.get("reputationLog") or [])[-30:]]
    rep_log.reverse()

    return {
        "user": {
            "id": str(current_user["_id"]),
            "username": current_user["username"],
            "email": current_user["email"],
            "displayName": current_user["displayName"],
            "reputation": current_user.get("reputation", 1),
            "isAdmin": current_user.get("isAdmin", False),
            "isBanned": current_user.get("isBanned", False),
        },
        "reputationLog": rep_log,
        "questions": questions,
        "answers": answers,
    }
