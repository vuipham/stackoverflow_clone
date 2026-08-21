"""
Seed dữ liệu: 1 tài khoản admin + các tài khoản test với reputation khác nhau
để demo được ngay các mốc đặc quyền (1, 15, 50, 125, 500, 2000) mà không cần vote thủ công.

Chạy: python -m app.seed
"""
import asyncio
from app.core.password import hash_password

from app.core.database import users_col

TEST_USERS = [
    {"username": "admin", "reputation": 1, "isAdmin": True, "displayName": "Quản trị viên"},
    {"username": "newbie", "reputation": 1, "displayName": "User mới (rep=1)"},
    {"username": "voter", "reputation": 20, "displayName": "User có thể upvote (rep=20)"},
    {"username": "commenter", "reputation": 60, "displayName": "User bình luận bài người khác (rep=60)"},
    {"username": "critic", "reputation": 130, "displayName": "User có thể downvote (rep=130)"},
    {"username": "editor", "reputation": 600, "displayName": "User có thể sửa bài người khác (rep=600)"},
    {"username": "veteran", "reputation": 2200, "displayName": "User kỳ cựu, full quyền (rep=2200)"},
]

DEFAULT_PASSWORD = "Test@123"


async def seed():
    password_hash = hash_password(DEFAULT_PASSWORD)

    for u in TEST_USERS:
        existed = await users_col.find_one({"username": u["username"]})
        if existed:
            print(f"[Seed] Bỏ qua (đã tồn tại): {u['username']}")
            continue

        await users_col.insert_one(
            {
                "username": u["username"],
                "email": f"{u['username']}@example.com",
                "passwordHash": password_hash,
                "displayName": u["displayName"],
                "isAdmin": u.get("isAdmin", False),
                "isBanned": False,
                "reputation": u["reputation"],
                "reputationLog": [],
            }
        )
        print(f"[Seed] Đã tạo user: {u['username']} (reputation={u['reputation']}, isAdmin={u.get('isAdmin', False)})")

    print(f"\nMật khẩu cho tất cả tài khoản test: {DEFAULT_PASSWORD}")
    print("Hoàn tất seed dữ liệu.")


if __name__ == "__main__":
    asyncio.run(seed())
