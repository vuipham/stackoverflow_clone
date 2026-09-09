"""
Badge Service — Tự động kiểm tra và trao Huy hiệu (Bronze, Silver, Gold) cho người dùng.
"""
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.core.database import user_badges_col, questions_col, answers_col, users_col

BADGES_DEF = {
    # Bronze Badges
    "STUDENT": {"name": "Student", "tier": "bronze", "description": "Đã đặt câu hỏi đầu tiên"},
    "TEACHER": {"name": "Teacher", "tier": "bronze", "description": "Đã đăng câu trả lời đầu tiên"},
    "SCHOLAR": {"name": "Scholar", "tier": "bronze", "description": "Chấp nhận câu trả lời đầu tiên"},
    "AUTOBIOGRAPHER": {"name": "Autobiographer", "tier": "bronze", "description": "Hoàn thiện hồ sơ cá nhân"},
    "NICE_QUESTION": {"name": "Nice Question", "tier": "bronze", "description": "Câu hỏi đạt 5 votes"},
    "NICE_ANSWER": {"name": "Nice Answer", "tier": "bronze", "description": "Câu trả lời đạt 5 votes"},
    "POPULAR_QUESTION": {"name": "Popular Question", "tier": "bronze", "description": "Câu hỏi đạt 100 lượt xem"},

    # Silver Badges
    "GOOD_QUESTION": {"name": "Good Question", "tier": "silver", "description": "Câu hỏi đạt 15 votes"},
    "GOOD_ANSWER": {"name": "Good Answer", "tier": "silver", "description": "Câu trả lời đạt 15 votes"},
    "FAMOUS_QUESTION": {"name": "Famous Question", "tier": "silver", "description": "Câu hỏi đạt 1,000 lượt xem"},

    # Gold Badges
    "GREAT_QUESTION": {"name": "Great Question", "tier": "gold", "description": "Câu hỏi đạt 30 votes"},
    "GREAT_ANSWER": {"name": "Great Answer", "tier": "gold", "description": "Câu trả lời đạt 30 votes"},
}


async def award_badge(user_id, badge_code: str):
    """Trao 1 badge cho user nếu chưa có."""
    if badge_code not in BADGES_DEF:
        return
    b_info = BADGES_DEF[badge_code]
    doc = {
        "userId": ObjectId(str(user_id)),
        "badgeCode": badge_code,
        "name": b_info["name"],
        "tier": b_info["tier"],
        "description": b_info["description"],
        "earnedAt": datetime.now(timezone.utc),
    }
    try:
        await user_badges_col.insert_one(doc)
    except DuplicateKeyError:
        pass  # Đã có badge này rồi, bỏ qua


async def evaluate_user_badges(user_id):
    """Kiểm tra điều kiện trao badge tự động cho user.

    Tối ưu cho dataset lớn: dùng aggregation ($match + $group với $max/$count)
    thay vì duyệt từng document rồi gọi insert_one trong vòng lặp. Trước đây với
    1M câu hỏi (1 tác giả sở hữu ~143k câu), vòng lặp sinh hàng trăm nghìn
    insert_one nối tiếp → mỗi request xem câu hỏi treo hàng chục giây.
    """
    uid = ObjectId(str(user_id))

    # --- Thống kê câu hỏi của user (cần index on authorId) ---
    q_stats = (
        await questions_col.aggregate(
            [
                {"$match": {"authorId": uid}},
                {
                    "$group": {
                        "_id": None,
                        "count": {"$sum": 1},
                        "maxScore": {"$max": "$voteScore"},
                        "maxViews": {"$max": "$viewCount"},
                        "hasAccepted": {
                            "$max": {
                                "$cond": [{"$ne": ["$acceptedAnswerId", None]}, 1, 0]
                            }
                        },
                    }
                },
            ]
        ).to_list(1)
    )
    qs = q_stats[0] if q_stats else None

    if qs and qs["count"] >= 1:
        await award_badge(uid, "STUDENT")
    if qs and qs["hasAccepted"]:
        await award_badge(uid, "SCHOLAR")
    if qs:
        score = qs["maxScore"] or 0
        views = qs["maxViews"] or 0
        if score >= 30:
            await award_badge(uid, "GREAT_QUESTION")
        if score >= 15:
            await award_badge(uid, "GOOD_QUESTION")
        if score >= 5:
            await award_badge(uid, "NICE_QUESTION")
        if views >= 1000:
            await award_badge(uid, "FAMOUS_QUESTION")
        if views >= 100:
            await award_badge(uid, "POPULAR_QUESTION")

    # --- Thống kê câu trả lời của user ---
    a_stats = (
        await answers_col.aggregate(
            [
                {"$match": {"authorId": uid}},
                {
                    "$group": {
                        "_id": None,
                        "count": {"$sum": 1},
                        "maxScore": {"$max": "$voteScore"},
                    }
                },
            ]
        ).to_list(1)
    )
    as_ = a_stats[0] if a_stats else None

    if as_ and as_["count"] >= 1:
        await award_badge(uid, "TEACHER")
    if as_:
        ascore = as_["maxScore"] or 0
        if ascore >= 30:
            await award_badge(uid, "GREAT_ANSWER")
        if ascore >= 15:
            await award_badge(uid, "GOOD_ANSWER")
        if ascore >= 5:
            await award_badge(uid, "NICE_ANSWER")


async def get_user_badges(user_id) -> list[dict]:
    """Trả về danh sách badges mà user đã đạt được."""
    cursor = user_badges_col.find({"userId": ObjectId(str(user_id))}).sort("earnedAt", -1)
    return [
        {
            "id": str(b["_id"]),
            "badgeCode": b["badgeCode"],
            "name": b["name"],
            "tier": b["tier"],
            "description": b["description"],
            "earnedAt": b["earnedAt"].isoformat(),
        }
        async for b in cursor
    ]
