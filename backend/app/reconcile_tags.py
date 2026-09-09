"""
Đồng bộ lại collection `tags` với dữ liệu thật trong `questions`.

Vấn đề đang sửa:
  seed_massive_questions.py --reset xóa toàn bộ `questions` nhưng KHÔNG cập nhật lại
tags_col. Kết quả: tags_col còn giữ những tag "ma" (vd. tensorflow qua=69) mà không còn
câu hỏi thật nào trong DB → tag cloud hiển thị các tag này nhưng bấm vào luôn rỗng.

Script này:
  1. Tính lại questionCount thật cho từng tag bằng cách aggregate trên `questions`.
  2. Upsert mọi tag thật vào `tags` (sửa count sai / tạo tag còn thiếu).
  3. Xóa các tag không còn câu hỏi thật nào (orphan/phantom như tensorflow) —
     bật `--keep-zero` để giữ lại (chỉ gán count=0).

Chạy:
  cd backend && venv/bin/python -m app.reconcile_tags
  cd backend && venv/bin/python -m app.reconcile_tags --keep-zero
"""
import argparse
import asyncio

from app.core.database import questions_col, tags_col


async def reconcile(keep_zero: bool = False) -> None:
    # 1) Tính count thật cho từng tag từ chính collection `questions`
    print("[ReconcileTags] Đang aggregate tag counts từ `questions`...")
    pipeline = [
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "c": {"$sum": 1}}},
    ]
    cursor = questions_col.aggregate(pipeline, allowDiskUse=True)
    real_counts: dict[str, int] = {}
    async for row in cursor:
        name: str = row["_id"]
        real_counts[name] = row["c"]
    print(f"[ReconcileTags] Tìm thấy {len(real_counts)} tag thật trong questions.")

    # 2) Đồng bộ tags_col với count thật
    for name, count in real_counts.items():
        await tags_col.update_one(
            {"name": name},
            {"$set": {"questionCount": count}, "$setOnInsert": {"description": ""}},
            upsert=True,
        )
    print(f"[ReconcileTags] Đã upsert {len(real_counts)} tag với questionCount thật.")

    # 3) Dọn tag ma (không có câu hỏi thật nào)
    orphan = [t async for t in tags_col.find({"name": {"$nin": list(real_counts.keys())}})]
    if orphan:
        names = [t["name"] for t in orphan]
        if keep_zero:
            await tags_col.update_many(
                {"name": {"$in": names}},
                {"$set": {"questionCount": 0}},
            )
            print(f"[ReconcileTags] Đã gán questionCount=0 cho {len(names)} tag ma (giữ lại): {', '.join(sorted(names))}")
        else:
            await tags_col.delete_many({"name": {"$in": names}})
            print(f"[ReconcileTags] Đã xóa {len(names)} tag ma không có câu hỏi thật: {', '.join(sorted(names))}")
    else:
        print("[ReconcileTags] Không có tag ma nào cần dọn.")

    print("[ReconcileTags] ✅ Hoàn tất đồng bộ tags.")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Đồng bộ lại tags với dữ liệu questions thật.")
    parser.add_argument("--keep-zero", action="store_true", help="Giữ lại tag ma (chỉ gán questionCount=0 thay vì xóa.")
    args = parser.parse_args()
    await reconcile(keep_zero=args.keep_zero)


if __name__ == "__main__":
    asyncio.run(main())
