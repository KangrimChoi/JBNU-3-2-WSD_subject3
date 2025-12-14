"""Review Schemas"""
from datetime import datetime
from pydantic import BaseModel, Field


# ==================== Request Schemas ====================

class ReviewCreate(BaseModel):
    """리뷰 작성 요청"""
    content: str = Field(
        ...,
        min_length=1,
        json_schema_extra={"example": "정말 유익한 책입니다.", "description": "리뷰 내용"}
    )
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        json_schema_extra={"example": 5, "description": "별점 (1~5)"}
    )


# ==================== Response Schemas ====================

class ReviewCreateResponse(BaseModel):
    """리뷰 작성 응답"""
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
