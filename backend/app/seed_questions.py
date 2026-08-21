"""
Nạp dataset mẫu (~400 tiêu đề câu hỏi đa chủ đề) vào MongoDB để có dữ liệu thật
cho việc build/test/benchmark module tìm kiếm ngữ nghĩa (TF-IDF + SBERT) ở Tuần 2.
Chạy SAU app.seed (cần có sẵn user để gán authorId).

Chạy: python -m app.seed_questions
"""
import asyncio
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from app.core.database import users_col, questions_col
from app.services.tag_service import sync_tags_on_create

DATASET_PATH = Path(__file__).parent / "data" / "questions_dataset.json"


async def seed_questions():
    users = [u async for u in users_col.find({})]
    if not users:
        print("[SeedQuestions] Chưa có user nào - hãy chạy `python -m app.seed` trước.")
        return

    existing_count = await questions_col.count_documents({})
    if existing_count > 0:
        print(f"[SeedQuestions] questions collection đã có {existing_count} bản ghi - bỏ qua để tránh trùng lặp.")
        print("               (Muốn nạp lại: xóa collection `questions` rồi chạy lại script này.)")
        return

    with open(DATASET_PATH, encoding="utf-8") as f:
        dataset = json.load(f)

    random.seed(7)
    docs = []
    now = datetime.now(timezone.utc)
    for item in dataset:
        author = random.choice(users)
        docs.append(
            {
                "title": item["title"],
                "body": item["body"],
                "tags": item["tags"],
                "authorId": author["_id"],
                "viewCount": random.randint(0, 200),
                "voteScore": 0,
                "answerCount": 0,
                "acceptedAnswerId": None,
                "isIndexed": False,  # module search Tuần 2 sẽ re-index toàn bộ
                "createdAt": now,
                "updatedAt": now,
            }
        )

    result = await questions_col.insert_many(docs)
    print(f"[SeedQuestions] Đã nạp {len(result.inserted_ids)} câu hỏi mẫu.")

    all_tags = [t for d in docs for t in d["tags"]]
    await sync_tags_on_create(all_tags)
    print("[SeedQuestions] Đã đồng bộ questionCount cho tags.")


if __name__ == "__main__":
    asyncio.run(seed_questions())
