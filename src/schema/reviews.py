"""Review Schemas"""
from datetime import datetime
from typing import Optional
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


class ReviewUpdate(BaseModel):
    """리뷰 수정 요청 - 모든 필드 선택적"""
    content: Optional[str] = Field(
        None,
        min_length=1,
        json_schema_extra={"example": "다른 책이랑 착각했네요.", "description": "수정할 리뷰 내용"}
    )
    rating: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        json_schema_extra={"example": 2, "description": "수정할 별점 (1~5)"}
    )


# ==================== Response Schemas ====================

class ReviewCreateResponse(BaseModel):
    """리뷰 작성 응답"""
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewUpdateResponse(BaseModel):
    """리뷰 수정 응답"""
    id: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewDeleteResponse(BaseModel):
    """리뷰 삭제 응답"""
    id: int


class ReviewLikeResponse(BaseModel):
    """리뷰 좋아요 응답"""
    review_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewAuthor(BaseModel):
    """리뷰 작성자 정보"""
    name: str


class ReviewListItem(BaseModel):
    """리뷰 목록 아이템"""
    id: int
    author: ReviewAuthor
    content: str
    rating: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewPagination(BaseModel):
    """리뷰 페이지네이션 정보"""
    page: int
    totalPages: int
    totalElements: int


class ReviewListResponse(BaseModel):
    """리뷰 목록 조회 응답"""
    reviews: list[ReviewListItem]
    pagination: ReviewPagination


class TopReviewItem(BaseModel):
    """Top-N 리뷰 아이템"""
    id: int
    author: ReviewAuthor
    content: str
    rating: int
    like_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TopReviewListResponse(BaseModel):
    """Top-N 리뷰 목록 응답"""
    reviews: list[TopReviewItem]
