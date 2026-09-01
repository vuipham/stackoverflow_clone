from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import votes_col, questions_col, answers_col
from app.core.security import get_current_user
from app.core.privileges import PRIVILEGE, REPUTATION_DELTA
from app.models.vote import VoteRequest
from app.services.reputation_service import adjust_reputation

router = APIRouter(prefix="/api/votes", tags=["votes"])

COLLECTION_BY_TYPE = {"question": questions_col, "answer": answers_col}


@router.post("", status_code=201)
async def cast_vote(payload: VoteRequest, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(payload.targetId):
        raise HTTPException(status_code=400, detail="targetId không hợp lệ")

    # Kiểm tra đặc quyền: upvote cần >=15, downvote cần >=125
    threshold = PRIVILEGE["UPVOTE"] if payload.value == 1 else PRIVILEGE["DOWNVOTE"]
    if current_user.get("reputation", 0) < threshold:
        action = "upvote" if payload.value == 1 else "downvote"
        raise HTTPException(
            status_code=403,
            detail={
                "error": f"Cần tối thiểu {threshold} điểm reputation để {action}",
                "currentReputation": current_user.get("reputation", 0),
            },
        )

    collection = COLLECTION_BY_TYPE[payload.targetType]
    target = await collection.find_one({"_id": ObjectId(payload.targetId)})
    if not target:
        raise HTTPException(status_code=404, detail="Không tìm thấy đối tượng để vote")

    if str(target["authorId"]) == str(current_user["_id"]):
        raise HTTPException(status_code=400, detail="Không thể tự vote bài của chính mình")

    target_oid = ObjectId(payload.targetId)
    existing_vote = await votes_col.find_one(
        {"userId": current_user["_id"], "targetType": payload.targetType, "targetId": target_oid}
    )
    current_score = target.get("voteScore", 0)

    if existing_vote:
        old_value = existing_vote["value"]

        if old_value == payload.value:
            # --- Hủy vote (cùng chiều) --- UC007 luồng đặc biệt bước 3
            await votes_col.delete_one({"_id": existing_vote["_id"]})
            new_score = current_score - old_value
            await collection.update_one({"_id": target["_id"]}, {"$set": {"voteScore": new_score}})

            # Hoàn trả reputation cho tác giả
            if old_value == 1:
                await adjust_reputation(
                    str(target["authorId"]), -REPUTATION_DELTA["UPVOTE_RECEIVED"],
                    "upvote_cancelled", str(target["_id"])
                )
            else:
                await adjust_reputation(
                    str(target["authorId"]), -REPUTATION_DELTA["DOWNVOTE_RECEIVED"],
                    "downvote_cancelled", str(target["_id"])
                )
                # Hoàn trả chi phí downvote cho người hủy
                await adjust_reputation(
                    str(current_user["_id"]), -REPUTATION_DELTA["DOWNVOTE_CAST"],
                    "downvote_cast_cancelled", str(target["_id"])
                )

            return {"message": "Đã hủy vote", "newVoteScore": new_score, "action": "cancelled"}

        else:
            # --- Đổi chiều vote --- UC007 luồng đặc biệt bước 3
            await votes_col.update_one(
                {"_id": existing_vote["_id"]},
                {"$set": {"value": payload.value, "updatedAt": datetime.now(timezone.utc)}},
            )
            new_score = current_score - old_value + payload.value
            await collection.update_one({"_id": target["_id"]}, {"$set": {"voteScore": new_score}})

            # Hoàn trả reputation cũ rồi áp reputation mới
            if old_value == 1:
                # upvote -> downvote
                await adjust_reputation(
                    str(target["authorId"]), -REPUTATION_DELTA["UPVOTE_RECEIVED"],
                    "upvote_reversed", str(target["_id"])
                )
                await adjust_reputation(
                    str(target["authorId"]), REPUTATION_DELTA["DOWNVOTE_RECEIVED"],
                    "downvote_received", str(target["_id"])
                )
                await adjust_reputation(
                    str(current_user["_id"]), REPUTATION_DELTA["DOWNVOTE_CAST"],
                    "downvote_cast", str(target["_id"])
                )
            else:
                # downvote -> upvote
                await adjust_reputation(
                    str(target["authorId"]), -REPUTATION_DELTA["DOWNVOTE_RECEIVED"],
                    "downvote_reversed", str(target["_id"])
                )
                await adjust_reputation(
                    str(target["authorId"]), REPUTATION_DELTA["UPVOTE_RECEIVED"],
                    "upvote_received", str(target["_id"])
                )
                # Hoàn trả chi phí downvote cũ
                await adjust_reputation(
                    str(current_user["_id"]), -REPUTATION_DELTA["DOWNVOTE_CAST"],
                    "downvote_cast_cancelled", str(target["_id"])
                )

            return {"message": "Đã đổi chiều vote", "newVoteScore": new_score, "action": "flipped"}

    # --- Vote mới ---
    vote_doc = {
        "userId": current_user["_id"],
        "targetType": payload.targetType,
        "targetId": target_oid,
        "value": payload.value,
        "createdAt": datetime.now(timezone.utc),
    }
    try:
        await votes_col.insert_one(vote_doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Bạn đã vote đối tượng này rồi")

    new_score = current_score + payload.value
    await collection.update_one({"_id": target["_id"]}, {"$set": {"voteScore": new_score}})

    # Cộng/trừ reputation cho tác giả bài viết được vote
    if payload.value == 1:
        author_delta, author_reason = REPUTATION_DELTA["UPVOTE_RECEIVED"], "upvote_received"
    else:
        author_delta, author_reason = REPUTATION_DELTA["DOWNVOTE_RECEIVED"], "downvote_received"
    await adjust_reputation(str(target["authorId"]), author_delta, author_reason, str(target["_id"]))

    # Chi phí -1 điểm cho người chủ động downvote (đúng thực tế Stack Overflow)
    if payload.value == -1:
        await adjust_reputation(
            str(current_user["_id"]), REPUTATION_DELTA["DOWNVOTE_CAST"], "downvote_cast", str(target["_id"])
        )

    return {"message": "Vote thành công", "newVoteScore": new_score, "action": "voted"}
