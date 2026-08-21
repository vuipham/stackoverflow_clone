from typing import Optional
from pydantic import BaseModel, Field


class TagCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=30)
    description: Optional[str] = ""


class TagUpdateRequest(BaseModel):
    description: Optional[str] = None


class TagOut(BaseModel):
    id: str
    name: str
    description: str
    questionCount: int
