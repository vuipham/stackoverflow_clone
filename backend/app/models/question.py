from typing import List, Optional
from pydantic import BaseModel, Field


class QuestionCreateRequest(BaseModel):
    title: str = Field(..., min_length=5)
    body: str = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list)


class QuestionUpdateRequest(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[List[str]] = None


class QuestionOut(BaseModel):
    id: str
    title: str
    body: str
    tags: List[str]
    authorId: str
    viewCount: int
    voteScore: int
    answerCount: int
    acceptedAnswerId: Optional[str] = None
    isIndexed: bool
    createdAt: str
    updatedAt: str
