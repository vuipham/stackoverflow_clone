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
tfidf_vocabulary_col = db["tfidf_vocabulary"]
search_benchmark_log_col = db["search_benchmark_log"]  # log thời gian phản hồi mỗi lần search - dùng cho báo cáo
bookmarks_col = db["bookmarks"]      # user lưu câu hỏi yêu thích
notifications_col = db["notifications"]  # thông báo real-time (answer, comment, accept, upvote)
revisions_col = db["revisions"]      # lịch sử chỉnh sửa bài viết (edit history)
user_badges_col = db["user_badges"]  # huy hiệu đạt được của user


async def ensure_indexes():
    """Tạo các index cần thiết - gọi 1 lần lúc khởi động app."""
    await users_col.create_index("username", unique=True)
    await users_col.create_index("email", unique=True)
    await users_col.create_index([("reputation", -1)])
    await users_col.create_index("isAdmin")

    await questions_col.create_index([("tags", 1)])
    await questions_col.create_index([("createdAt", -1)])
    await questions_col.create_index("isIndexed")
    # Badge/reputation truy vấn theo tác giả - thiếu index này sẽ quét toàn bộ
    # collection (1M+ doc) mỗi lần xem câu hỏi, gây treo rất lâu.
    await questions_col.create_index("authorId")

    await answers_col.create_index("questionId")
    await answers_col.create_index("authorId")
    await comments_col.create_index([("targetType", 1), ("targetId", 1)])
    await votes_col.create_index([("userId", 1), ("targetType", 1), ("targetId", 1)], unique=True)
    await tags_col.create_index("name", unique=True)

    # Bookmarks: mỗi user chỉ bookmark 1 câu hỏi 1 lần
    await bookmarks_col.create_index([("userId", 1), ("questionId", 1)], unique=True)
    await bookmarks_col.create_index([("userId", 1), ("createdAt", -1)])

    # Notifications: index theo recipient + unread để count nhanh
    await notifications_col.create_index([("recipientId", 1), ("isRead", 1), ("createdAt", -1)])
    await notifications_col.create_index([("recipientId", 1), ("createdAt", -1)])

    # Revisions & Badges
    await revisions_col.create_index([("targetType", 1), ("targetId", 1), ("createdAt", -1)])
    await user_badges_col.create_index([("userId", 1), ("badgeCode", 1)], unique=True)
    await user_badges_col.create_index([("userId", 1), ("earnedAt", -1)])
