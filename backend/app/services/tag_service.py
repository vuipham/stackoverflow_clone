"""
Đồng bộ collection `tags` với trường `tags` (mảng string) trên `questions`.
Tag được tạo "hữu cơ" khi user gõ tag mới lúc đăng câu hỏi (đúng hành vi Stack Overflow
thật - user tự do gắn tag mới), Admin chỉ cần vào sửa mô tả / xóa tag rác sau đó.
"""
from app.core.database import tags_col


async def sync_tags_on_create(tag_names: list[str]):
    """Gọi khi tạo câu hỏi mới: upsert từng tag, +1 questionCount."""
    for name in tag_names:
        await tags_col.update_one(
            {"name": name},
            {"$setOnInsert": {"description": ""}, "$inc": {"questionCount": 1}},
            upsert=True,
        )


async def sync_tags_on_delete(tag_names: list[str]):
    """Gọi khi xóa câu hỏi hoặc đổi tag: -1 questionCount (không xóa tag doc, admin tự dọn)."""
    for name in tag_names:
        await tags_col.update_one({"name": name}, {"$inc": {"questionCount": -1}})


async def sync_tags_on_update(old_tags: list[str], new_tags: list[str]):
    """Gọi khi sửa câu hỏi đổi danh sách tag: chỉ +/- phần chênh lệch."""
    old_set, new_set = set(old_tags), set(new_tags)
    removed = old_set - new_set
    added = new_set - old_set
    if removed:
        await sync_tags_on_delete(list(removed))
    if added:
        await sync_tags_on_create(list(added))
