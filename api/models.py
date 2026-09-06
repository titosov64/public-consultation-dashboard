from pydantic import BaseModel
from typing import List

class Comment(BaseModel):
    id: str
    consultation_id: int
    text: str
    author: str | None = None
    timestamp: str | None = None
    source_url: str | None = None
    is_misattributed: bool

class Stats(BaseModel):
    total_comments: int
    misattributed_comments: int
    consultation_id: int

class CommentsResponse(BaseModel):
    comments: List[Comment]
