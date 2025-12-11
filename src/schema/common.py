"""공통 응답 스키마"""
from datetime import datetime
from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel

T = TypeVar("T")


# ==================== 성공 응답 ====================

class APIResponse(BaseModel, Generic[T]):
    """공통 API 응답 래퍼"""
    isSuccess: bool
    message: str
    payload: Optional[T] = None


# ==================== 에러 응답 ====================

class ErrorResponse(BaseModel):
    """에러 응답"""
    timestamp: datetime
    path: str
    status: int
    code: str
    message: str
    details: Optional[dict[str, Any]] = None


# ==================== 페이지네이션 응답 ====================

class PagedResponse(BaseModel, Generic[T]):
    """페이지네이션 응답"""
    content: List[T]
    page: int
    size: int
    totalElements: int
    totalPages: int
    sort: Optional[str] = None
