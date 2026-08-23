"""
Nạp thêm N câu hỏi (mặc định 5000) vào MongoDB để stress-test tốc độ tìm kiếm khi
dataset lớn hơn nhiều so với 400 câu ban đầu. Dùng lại bộ template trong
questions_dataset.json, nhân bản thêm hậu tố số thứ tự để tránh trùng hoàn toàn
(không cần nội dung đa dạng - mục đích chỉ là đo tốc độ với khối lượng lớn).

Chạy (mặc định thêm 5000 câu):
    python -m app.seed_bulk
Hoặc chỉ định số lượng khác:
    python -m app.seed_bulk 20000

Sau khi nạp xong, script TỰ ĐỘNG reindex TF-IDF và chạy thử vài truy vấn để in
ra thời gian phản hồi thực tế - không cần gọi API thủ công.
"""
import asyncio
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from app.core.database import users_col, questions_col
from app.services.tag_service import sync_tags_on_create
from app.services.search import tfidf_service

DATASET_PATH = Path(__file__).parent / "data" / "questions_dataset.json"

# Vài câu truy vấn mẫu để đo tốc độ search sau khi nạp xong
SAMPLE_QUERIES = [
    "cách kết nối cơ sở dữ liệu",
    "lỗi khi deploy production",
    "tối ưu hiệu năng hệ thống",
    "so sánh hai công nghệ",
    "xử lý ngôn ngữ tự nhiên",
]


async def seed_bulk(target_count: int):
    users = [u async for u in users_col.find({})]
    if not users:
        print("[SeedBulk] Chưa có user nào - hãy chạy `python -m app.seed` trước.")
        return

    with open(DATASET_PATH, encoding="utf-8") as f:
        base_dataset = json.load(f)

    print(f"[SeedBulk] Sẽ tạo thêm {target_count} câu hỏi (nhân bản từ {len(base_dataset)} mẫu gốc)...")

    random.seed(123)
    now = datetime.now(timezone.utc)
    batch = []
    batch_size = 1000
    inserted = 0
    all_tags: list[str] = []

    t0 = time.perf_counter()
    for i in range(target_count):
        item = base_dataset[i % len(base_dataset)]
        author = random.choice(users)
        title = f"{item['title']} (#{i + 1})"
        doc = {
            "title": title,
            "body": item["body"],
            "tags": item["tags"],
            "authorId": author["_id"],
            "viewCount": random.randint(0, 200),
            "voteScore": 0,
            "answerCount": 0,
            "acceptedAnswerId": None,
            "isIndexed": False,
            "createdAt": now,
            "updatedAt": now,
        }
        batch.append(doc)
        all_tags.extend(item["tags"])

        if len(batch) >= batch_size:
            await questions_col.insert_many(batch)
            inserted += len(batch)
            print(f"[SeedBulk]   ...đã nạp {inserted}/{target_count}")
            batch = []

    if batch:
        await questions_col.insert_many(batch)
        inserted += len(batch)

    insert_elapsed = time.perf_counter() - t0
    print(f"[SeedBulk] Đã nạp xong {inserted} câu hỏi trong {insert_elapsed:.2f}s")

    await sync_tags_on_create(all_tags)

    total_count = await questions_col.count_documents({})
    print(f"[SeedBulk] Tổng số câu hỏi trong DB hiện tại: {total_count}")

    print("\n[SeedBulk] Đang reindex TF-IDF cho toàn bộ dataset (có thể mất vài giây với dataset lớn)...")
    t0 = time.perf_counter()
    stats = await tfidf_service.reindex_all()
    reindex_elapsed = time.perf_counter() - t0
    print(f"[SeedBulk] Reindex xong: {stats} (tổng thời gian đo ngoài: {reindex_elapsed:.2f}s)")

    print("\n[SeedBulk] Đo tốc độ search thực tế với vài truy vấn mẫu:")
    print("-" * 70)
    for q in SAMPLE_QUERIES:
        t0 = time.perf_counter()
        results = tfidf_service.search(q, top_k=10)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        print(f"  '{q}'")
        print(f"    -> {len(results)} kết quả, {elapsed_ms:.2f}ms")
    print("-" * 70)
    print(f"\n[SeedBulk] Hoàn tất. Dataset hiện có {total_count} câu hỏi - thử lại các truy vấn")
    print("           trên qua API (/api/search/tfidf) hoặc frontend /search để so sánh cảm nhận.")


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    asyncio.run(seed_bulk(count))
