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


class CommentUpdate(BaseModel):
    """댓글 수정 요청"""
    content: str = Field(
        ...,
        min_length=1,
        json_schema_extra={"example": "수정된 댓글 내용입니다.", "description": "수정할 댓글 내용"}
    )


# ==================== Response Schemas ====================

class CommentCreateResponse(BaseModel):
    """댓글 작성 응답"""
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CommentUpdateResponse(BaseModel):
    """댓글 수정 응답"""
    id: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class CommentDeleteResponse(BaseModel):
    """댓글 삭제 응답"""
    id: int


class CommentAuthor(BaseModel):
    """댓글 작성자 정보"""
    name: str


class CommentListItem(BaseModel):
    """댓글 목록 아이템"""
    id: int
    author: CommentAuthor
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CommentPagination(BaseModel):
    """댓글 페이지네이션 정보"""
    page: int
    totalPages: int
    totalElements: int


class CommentListResponse(BaseModel):
    """댓글 목록 조회 응답"""
    comments: list[CommentListItem]
    pagination: CommentPagination
