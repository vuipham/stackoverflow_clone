from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.mongo_db_name]

# Các collection dùng chung toàn app - import db từ đây ở mọi router/service
users_col = db["users"]
questions_col = db["questions"]
answers_col = db["answers"]
comments_col = db["comments"]
votes_col = db["votes"]
tags_col = db["tags"]
question_vectors_tfidf_col = db["question_vectors_tfidf"]
question_vectors_sbert_col = db["question_vectors_sbert"]
tfidf_vocabulary_col = db["tfidf_vocabulary"]
search_benchmark_log_col = db["search_benchmark_log"]  # log thời gian phản hồi mỗi lần search - dùng cho báo cáo


async def ensure_indexes():
    """Tạo các index cần thiết - gọi 1 lần lúc khởi động app."""
    await users_col.create_index("username", unique=True)
    await users_col.create_index("email", unique=True)
    await users_col.create_index([("reputation", -1)])
    await users_col.create_index("isAdmin")

    await questions_col.create_index([("tags", 1)])
    await questions_col.create_index([("createdAt", -1)])
    await questions_col.create_index("isIndexed")

    await answers_col.create_index("questionId")
    await comments_col.create_index([("targetType", 1), ("targetId", 1)])
    await votes_col.create_index([("userId", 1), ("targetType", 1), ("targetId", 1)], unique=True)
    await tags_col.create_index("name", unique=True)
