"""
Dùng thư viện `bcrypt` trực tiếp thay vì qua `passlib` — passlib 1.7.4 không tương thích
với bcrypt >= 4.1 (lỗi AttributeError: module 'bcrypt' has no attribute '__about__').
"""
import bcrypt


def hash_password(plain_password: str) -> str:
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
