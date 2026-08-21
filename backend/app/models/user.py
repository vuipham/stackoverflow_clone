from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class ReputationLogEntry(BaseModel):
    delta: int
    reason: str  # 'upvote_received' | 'downvote_received' | 'downvote_cast' | 'answer_accepted' | 'admin_adjust'
    refId: Optional[str] = None
    at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserRegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    displayName: Optional[str] = None


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserPublic(BaseModel):
    id: str
    username: str
    email: str
    displayName: str
    reputation: int
    isAdmin: bool


class TokenResponse(BaseModel):
    token: str
    user: UserPublic
