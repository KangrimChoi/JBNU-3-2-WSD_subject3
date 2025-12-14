"""Comment Schemas"""
from datetime import datetime
from pydantic import BaseModel, Field


# ==================== Request Schemas ====================

class CommentCreate(BaseModel):
    """댓글 작성 요청"""
    content: str = Field(
        ...,
        min_length=1,
        json_schema_extra={"example": "좋은 책이네요!", "description": "댓글 내용"}
    )


# ==================== Response Schemas ====================

class CommentCreateResponse(BaseModel):
    """댓글 작성 응답"""
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
