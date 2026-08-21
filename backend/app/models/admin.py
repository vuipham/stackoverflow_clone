from typing import Optional
from pydantic import BaseModel


class AdminAdjustReputationRequest(BaseModel):
    delta: int
    reason: str = "admin_adjust"


class AdminBanRequest(BaseModel):
    isBanned: bool


class AdminUserOut(BaseModel):
    id: str
    username: str
    email: str
    displayName: str
    reputation: int
    isAdmin: bool
    isBanned: bool
    createdAt: Optional[str] = None
