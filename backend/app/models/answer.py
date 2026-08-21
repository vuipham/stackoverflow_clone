from typing import Optional
from pydantic import BaseModel, Field


class AnswerCreateRequest(BaseModel):
    body: str = Field(..., min_length=1)


class AnswerUpdateRequest(BaseModel):
    body: str = Field(..., min_length=1)


class AnswerOut(BaseModel):
    id: str
    questionId: str
    authorId: str
    body: str
    voteScore: int
    isAccepted: bool
    createdAt: str
