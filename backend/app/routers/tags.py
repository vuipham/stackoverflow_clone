from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import tags_col, questions_col
from app.core.security import require_admin
from app.models.tag import TagCreateRequest, TagUpdateRequest, TagMergeRequest

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
    """Sửa mô tả và/hoặc đổi tên tag — UC011."""
    if not ObjectId.is_valid(tag_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    t = await tags_col.find_one({"_id": ObjectId(tag_id)})
    if not t:
        raise HTTPException(status_code=404, detail="Không tìm thấy tag")

    update_fields: dict = {}
    if payload.description is not None:
        update_fields["description"] = payload.description

    if payload.name is not None:
        new_name = payload.name.lower().strip()
        if new_name != t["name"]:
            conflict = await tags_col.find_one({"name": new_name})
            if conflict:
                raise HTTPException(status_code=409, detail=f"Tag tên '{new_name}' đã tồn tại")
            update_fields["name"] = new_name
            # Cập nhật tên tag trong tất cả câu hỏi đang dùng tag cũ
            await questions_col.update_many(
                {"tags": t["name"]},
                {"$set": {"tags.$[elem]": new_name}},
                array_filters=[{"elem": t["name"]}],
            )

    if update_fields:
        await tags_col.update_one({"_id": t["_id"]}, {"$set": update_fields})

    updated = await tags_col.find_one({"_id": t["_id"]})
    return {"tag": serialize_tag(updated)}


@router.post("/merge", status_code=200)
async def merge_tags(payload: TagMergeRequest, _admin: dict = Depends(require_admin)):
    """
    Gộp tag nguồn (source) vào tag đích (target) — UC011.
    Sau khi gộp: tag nguồn bị xóa, mọi câu hỏi dùng tag nguồn được cập nhật sang tag đích.
    """
    if not ObjectId.is_valid(payload.sourceTagId) or not ObjectId.is_valid(payload.targetTagId):
        raise HTTPException(status_code=400, detail="ID tag không hợp lệ")
    if payload.sourceTagId == payload.targetTagId:
        raise HTTPException(status_code=400, detail="Tag nguồn và tag đích không được trùng nhau")

    source = await tags_col.find_one({"_id": ObjectId(payload.sourceTagId)})
    target = await tags_col.find_one({"_id": ObjectId(payload.targetTagId)})
    if not source:
        raise HTTPException(status_code=404, detail="Không tìm thấy tag nguồn")
    if not target:
        raise HTTPException(status_code=404, detail="Không tìm thấy tag đích")

    # Tìm các câu hỏi có tag nguồn nhưng CHƯA có tag đích (để tránh trùng)
    questions_source_only = await questions_col.count_documents(
        {"tags": source["name"], "$nor": [{"tags": target["name"]}]}
    )
    # Câu hỏi có cả hai tag: xóa tag nguồn khỏi array
    await questions_col.update_many(
        {"tags": source["name"], "$and": [{"tags": target["name"]}]},
        {"$pull": {"tags": source["name"]}},
    )
    # Câu hỏi chỉ có tag nguồn: đổi sang tag đích
    await questions_col.update_many(
        {"tags": source["name"]},
        {"$set": {"tags.$[elem]": target["name"]}},
        array_filters=[{"elem": source["name"]}],
    )

    # Cộng questionCount từ source vào target rồi xóa source
    new_count = target.get("questionCount", 0) + questions_source_only
    await tags_col.update_one({"_id": target["_id"]}, {"$set": {"questionCount": new_count}})
    await tags_col.delete_one({"_id": source["_id"]})

    updated_target = await tags_col.find_one({"_id": target["_id"]})
    return {
        "message": f"Đã gộp tag '{source['name']}' vào '{target['name']}'",
        "tag": serialize_tag(updated_target),
        "questionsMigrated": questions_source_only,
    }


@router.delete("/{tag_id}")
async def delete_tag(tag_id: str, _admin: dict = Depends(require_admin)):
    if not ObjectId.is_valid(tag_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    result = await tags_col.delete_one({"_id": ObjectId(tag_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy tag")
    return {"message": "Đã xóa tag (lưu ý: không tự xóa tag khỏi các câu hỏi đã gắn)"}
