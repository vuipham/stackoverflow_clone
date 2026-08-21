"""
Bảng ngưỡng đặc quyền theo reputation - mô phỏng đúng cơ chế thực tế của Stack Overflow
(rút gọn cho phạm vi đồ án).
"""

PRIVILEGE = {
    "ASK_ANSWER": 1,
    "UPVOTE": 15,
    "COMMENT_ON_OTHERS": 50,
    "DOWNVOTE": 125,
    "EDIT_OTHERS_POST": 500,
    "DELETE_OTHERS_QUESTION": 2000,
}

# Số điểm reputation thay đổi ứng với từng sự kiện
REPUTATION_DELTA = {
    "UPVOTE_RECEIVED": 10,
    "DOWNVOTE_RECEIVED": -2,
    "DOWNVOTE_CAST": -1,  # "chi phí" khi chủ động downvote người khác, đúng như SO thật
    "ANSWER_ACCEPTED": 15,
}
