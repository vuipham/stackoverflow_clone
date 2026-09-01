from typing import Optional
from pydantic import BaseModel, Field


class TagCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=30)
    description: Optional[str] = ""


class TagUpdateRequest(BaseModel):
    description: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=30)


class TagMergeRequest(BaseModel):
    sourceTagId: str  # tag bị gộp vào target rồi xóa
    targetTagId: str  # tag giữ lại


class TagOut(BaseModel):
    id: str
    name: str
    description: str
    questionCount: int
