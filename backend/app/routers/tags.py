from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import tags_col
from app.core.security import require_admin
from app.models.tag import TagCreateRequest, TagUpdateRequest

router = APIRouter(prefix="/api/tags", tags=["tags"])


def serialize_tag(t: dict) -> dict:
    return {
        "id": str(t["_id"]),
        "name": t["name"],
        "description": t.get("description", ""),
        "questionCount": t.get("questionCount", 0),
    }


@router.get("")
async def list_tags():
    cursor = tags_col.find({}).sort("questionCount", -1)
    tags = [serialize_tag(t) async for t in cursor]
    return {"tags": tags}


@router.post("", status_code=201)
async def create_tag(payload: TagCreateRequest, _admin: dict = Depends(require_admin)):
    name = payload.name.lower().strip()
    existed = await tags_col.find_one({"name": name})
    if existed:
        raise HTTPException(status_code=409, detail="Tag đã tồn tại")
    doc = {"name": name, "description": payload.description or "", "questionCount": 0}
    result = await tags_col.insert_one(doc)
    doc["_id"] = result.inserted_id
    return {"tag": serialize_tag(doc)}


@router.put("/{tag_id}")
async def update_tag(tag_id: str, payload: TagUpdateRequest, _admin: dict = Depends(require_admin)):
    if not ObjectId.is_valid(tag_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    t = await tags_col.find_one({"_id": ObjectId(tag_id)})
    if not t:
        raise HTTPException(status_code=404, detail="Không tìm thấy tag")
    if payload.description is not None:
        await tags_col.update_one({"_id": t["_id"]}, {"$set": {"description": payload.description}})
    updated = await tags_col.find_one({"_id": t["_id"]})
    return {"tag": serialize_tag(updated)}


@router.delete("/{tag_id}")
async def delete_tag(tag_id: str, _admin: dict = Depends(require_admin)):
    if not ObjectId.is_valid(tag_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    result = await tags_col.delete_one({"_id": ObjectId(tag_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy tag")
    return {"message": "Đã xóa tag (lưu ý: không tự xóa tag khỏi các câu hỏi đã gắn)"}
