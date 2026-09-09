"""
Notification service — tạo thông báo cho người dùng khi có sự kiện liên quan.
Các loại event: new_answer, new_comment, answer_accepted, question_upvoted, answer_upvoted.

Thiết kế: push vào collection `notifications`, không dùng WebSocket (polling từ frontend).
Mỗi notification chứa đủ thông tin để render mà không cần join thêm.
"""
from datetime import datetime, timezone
from bson import ObjectId

from app.core.database import notifications_col


async def push(
    recipient_id,          # ObjectId hoặc str của người nhận
    event_type: str,       # 'new_answer' | 'new_comment' | 'answer_accepted' | 'question_upvoted' | 'answer_upvoted'
    actor_name: str,       # displayName của người trigger
    question_id: str,
    question_title: str,
    ref_id: str | None = None,   # answerId hoặc commentId nếu có
):
    """Tạo 1 notification. Nếu recipient_id trùng actor thì bỏ qua (không tự thông báo)."""
    if str(recipient_id) == str(ref_id):  # guard thừa, chặn self-notify
        return
    doc = {
        "recipientId": ObjectId(str(recipient_id)),
        "eventType": event_type,
        "actorName": actor_name,
        "questionId": question_id,
        "questionTitle": question_title,
        "refId": ref_id,
        "isRead": False,
        "createdAt": datetime.now(timezone.utc),
    }
    await notifications_col.insert_one(doc)
