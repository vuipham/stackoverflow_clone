from datetime import datetime, timezone
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import comments_col, questions_col, answers_col
from app.core.security import get_current_user
from app.core.privileges import PRIVILEGE
from app.models.comment import CommentCreateRequest

router = APIRouter(prefix="/api/comments", tags=["comments"])

COLLECTION_BY_TYPE = {"question": questions_col, "answer": answers_col}


def serialize_comment(c: dict) -> dict:
    return {
        "id": str(c["_id"]),
        "targetType": c["targetType"],
        "targetId": str(c["targetId"]),
        "authorId": str(c["authorId"]),
        "content": c["content"],
        "createdAt": c["createdAt"].isoformat(),
    }


@router.get("")
async def list_comments(targetType: str = Query(...), targetId: str = Query(...)):
    if targetType not in COLLECTION_BY_TYPE or not ObjectId.is_valid(targetId):
        raise HTTPException(status_code=400, detail="targetType/targetId không hợp lệ")
    cursor = comments_col.find({"targetType": targetType, "targetId": ObjectId(targetId)}).sort("createdAt", 1)
    comments = [serialize_comment(c) async for c in cursor]
    return {"comments": comments}


@router.post("", status_code=201)
async def create_comment(payload: CommentCreateRequest, current_user: dict = Depends(get_current_user)):
    if payload.targetType not in COLLECTION_BY_TYPE or not ObjectId.is_valid(payload.targetId):
        raise HTTPException(status_code=400, detail="targetType/targetId không hợp lệ")

    collection = COLLECTION_BY_TYPE[payload.targetType]
    target = await collection.find_one({"_id": ObjectId(payload.targetId)})
    if not target:
        raise HTTPException(status_code=404, detail="Không tìm thấy đối tượng để bình luận")

    is_owner = str(target["authorId"]) == str(current_user["_id"])
    # Dưới 50 reputation chỉ bình luận được bài của chính mình (đúng cơ chế thật của Stack Overflow)
    if not is_owner and current_user.get("reputation", 0) < PRIVILEGE["COMMENT_ON_OTHERS"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": f"Cần tối thiểu {PRIVILEGE['COMMENT_ON_OTHERS']} điểm reputation để bình luận bài của người khác",
                "currentReputation": current_user.get("reputation", 0),
            },
        )

    doc = {
        "targetType": payload.targetType,
        "targetId": ObjectId(payload.targetId),
        "authorId": current_user["_id"],
        "content": payload.content,
        "createdAt": datetime.now(timezone.utc),
    }
    result = await comments_col.insert_one(doc)
    doc["_id"] = result.inserted_id
    return {"comment": serialize_comment(doc)}


@router.delete("/{comment_id}")
async def delete_comment(comment_id: str, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(comment_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    c = await comments_col.find_one({"_id": ObjectId(comment_id)})
    if not c:
        raise HTTPException(status_code=404, detail="Không tìm thấy bình luận")

    is_owner = str(c["authorId"]) == str(current_user["_id"])
    if not is_owner and not current_user.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Chỉ tác giả bình luận hoặc Admin mới được xóa")

    await comments_col.delete_one({"_id": c["_id"]})
    return {"message": "Đã xóa bình luận"}
