from typing import Literal
from pydantic import BaseModel, Field


class CommentCreateRequest(BaseModel):
    targetType: Literal["question", "answer"]
    targetId: str
    content: str = Field(..., min_length=1, max_length=1000)


class CommentOut(BaseModel):
    id: str
    targetType: str
    targetId: str
    authorId: str
    content: str
    createdAt: str
