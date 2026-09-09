from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import users_col, questions_col, answers_col
from app.core.security import get_current_user
from app.models.user import UserUpdateRequest

router = APIRouter(prefix="/api/users", tags=["users"])


def serialize_rep_log(entry: dict) -> dict:
    return {
        "delta": entry.get("delta", 0),
        "reason": entry.get("reason", ""),
        "refId": str(entry["refId"]) if entry.get("refId") is not None else None,
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


from app.services import badge_service
from fastapi import Query


@router.get("")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    q: str = Query("", description="Tìm kiếm tên người dùng"),
    sort: str = Query("reputation", regex="^(reputation|newest)$"),
):
    """Bảng xếp hạng người dùng (Users Leaderboard) — phân trang, lọc theo tên, sắp xếp theo reputation hoặc mới nhất."""
    filt = {"isBanned": {"$ne": True}}
    if q.strip():
        filt["displayName"] = {"$regex": q.strip(), "$options": "i"}

    sort_spec = [("reputation", -1), ("_id", -1)] if sort == "reputation" else [("_id", -1)]
    total = await users_col.count_documents(filt)
    cursor = users_col.find(filt).sort(sort_spec).skip((page - 1) * limit).limit(limit)

    users_list = []
    async for u in cursor:
        badges = await badge_service.get_user_badges(u["_id"])
        users_list.append({
            "id": str(u["_id"]),
            "username": u["username"],
            "displayName": u.get("displayName", u["username"]),
            "reputation": u.get("reputation", 1),
            "isAdmin": u.get("isAdmin", False),
            "badgeCount": len(badges),
            "badges": badges[:3],  # top 3 badges gần nhất
            "createdAt": u["_id"].generation_time.isoformat(),
        })

    return {
        "users": users_list,
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": max(1, (total + limit - 1) // limit),
    }


@router.get("/me/profile")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Hồ sơ cá nhân của chính mình — UC009, bao gồm email và badges."""
    await badge_service.evaluate_user_badges(current_user["_id"])
    badges = await badge_service.get_user_badges(current_user["_id"])

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
        "badges": badges,
        "reputationLog": rep_log,
        "questions": questions,
        "answers": answers,
    }


@router.patch("/me")
async def update_my_profile(
    payload: UserUpdateRequest, current_user: dict = Depends(get_current_user)
):
    """Cập nhật hồ sơ cá nhân của chính mình — UC009 (Chỉnh sửa hồ sơ).
    Chỉ cho phép sửa displayName / email. username, reputation, isAdmin bất biến."""
    update: dict = {}

    if payload.displayName is not None:
        name = payload.displayName.strip()
        if not (3 <= len(name) <= 50):
            raise HTTPException(status_code=400, detail="Tên hiển thị phải từ 3 đến 50 ký tự")
        update["displayName"] = name

    if payload.email is not None:
        email = payload.email.strip().lower()
        if email != current_user.get("email"):
            conflict = await users_col.find_one({"email": email, "_id": {"$ne": current_user["_id"]}})
            if conflict:
                raise HTTPException(status_code=409, detail="Email đã được sử dụng bởi tài khoản khác")
        update["email"] = email

    if not update:
        raise HTTPException(status_code=400, detail="Không có thông tin nào cần cập nhật")

    await users_col.update_one({"_id": current_user["_id"]}, {"$set": update})
    updated = await users_col.find_one({"_id": current_user["_id"]})
    return {
        "user": {
            "id": str(updated["_id"]),
            "username": updated["username"],
            "email": updated["email"],
            "displayName": updated["displayName"],
            "reputation": updated.get("reputation", 1),
            "isAdmin": updated.get("isAdmin", False),
        },
        "message": "Đã cập nhật hồ sơ thành công",
    }


@router.get("/{user_id}")
async def get_user_profile(user_id: str):
    """Hồ sơ công khai của một user — UC009."""
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    user = await users_col.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    await badge_service.evaluate_user_badges(user["_id"])
    badges = await badge_service.get_user_badges(user["_id"])

    questions_cursor = questions_col.find({"authorId": user["_id"]}).sort("createdAt", -1).limit(50)
    questions = [serialize_question_brief(q) async for q in questions_cursor]

    answers_cursor = answers_col.find({"authorId": user["_id"]}).sort("createdAt", -1).limit(50)
    answers = [serialize_answer_brief(a) async for a in answers_cursor]

    rep_log = [serialize_rep_log(e) for e in (user.get("reputationLog") or [])[-30:]]
    rep_log.reverse()

    return {
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "displayName": user["displayName"],
            "reputation": user.get("reputation", 1),
            "isAdmin": user.get("isAdmin", False),
            "isBanned": user.get("isBanned", False),
        },
        "badges": badges,
        "reputationLog": rep_log,
        "questions": questions,
        "answers": answers,
    }
