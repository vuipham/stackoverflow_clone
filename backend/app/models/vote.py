from typing import Literal
from pydantic import BaseModel


class VoteRequest(BaseModel):
    targetType: Literal["question", "answer"]
    targetId: str
    value: Literal[1, -1]
