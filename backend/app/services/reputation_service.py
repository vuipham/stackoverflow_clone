from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from app.core.database import users_col


async def adjust_reputation(user_id: str, delta: int, reason: str, ref_id: Optional[str] = None):
    """
    Cộng/trừ reputation cho 1 user và ghi log lại lý do.
    Dùng chung cho mọi nơi có thay đổi reputation: vote, accept-answer, admin chỉnh tay...
    """
    log_entry = {
        "delta": delta,
        "reason": reason,
        "refId": ObjectId(ref_id) if ref_id else None,
        "at": datetime.now(timezone.utc),
    }

    await users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"reputation": delta}, "$push": {"reputationLog": log_entry}},
    )

    # Không cho reputation xuống dưới 1 (đúng hành vi thực tế của Stack Overflow)
    user = await users_col.find_one({"_id": ObjectId(user_id)})
    if user and user.get("reputation", 1) < 1:
        await users_col.update_one({"_id": ObjectId(user_id)}, {"$set": {"reputation": 1}})

    return await users_col.find_one({"_id": ObjectId(user_id)})
