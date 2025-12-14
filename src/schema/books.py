"""Book Schemas"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


# ==================== Request Schemas ====================

class BookCreate(BaseModel):
    """도서 등록 요청"""
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        json_schema_extra={"example": "앵무새 죽이기", "description": "도서 제목"}
    )
    categories: list[str] = Field(
        ...,
        min_length=1,
        json_schema_extra={"example": ["문학", "영미소설"], "description": "도서 카테고리"}
    )
    authors: list[str] = Field(
        ...,
        min_length=1,
        json_schema_extra={"example": ["하퍼 리"], "description": "도서 저자"}
    )
    description: Optional[str] = Field(
        None,
        json_schema_extra={"example": "인종차별이 심했던 앨라배마 주를 배경으로 다룬 소설이다.", "description": "도서 설명"}
    )
    isbn: str = Field(
        ...,
        min_length=10,
        max_length=13,
        json_schema_extra={"example": "9780060935467", "description": "국제 표준 도서 번호 (10자리 또는 13자리)"}
    )
    cover_image_url: Optional[str] = Field(
        None,
        max_length=255,
        json_schema_extra={"example": "https://example.com/images/book.png", "description": "표지 이미지 URL"}
    )
    price: Decimal = Field(
        ...,
        gt=0,
        json_schema_extra={"example": 35000, "description": "도서 가격"}
    )
    publication_date: Optional[date] = Field(
        None,
        json_schema_extra={"example": "1960-07-11", "description": "출판 날짜"}
    )


# ==================== Response Schemas ====================

class BookCreateResponse(BaseModel):
    """도서 등록 응답"""
    id: int
    title: str
    categories: list[str]
    authors: list[str]
    description: Optional[str] = None
    isbn: str
    cover_image_url: Optional[str] = None
    price: Decimal
    publication_date: Optional[date] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BookListItem(BaseModel):
    """도서 목록 아이템"""
    id: int
    title: str
    categories: list[str]
    authors: list[str]
    description: Optional[str] = None
    isbn: str
    cover_image_url: Optional[str] = None
    price: Decimal
    publication_date: Optional[date] = None


class BookPagination(BaseModel):
    """도서 페이지네이션 정보"""
    total_books: int
    total_pages: int
    current_page: int
    page_size: int
    page_sort: int


class BookListResponse(BaseModel):
    """도서 목록 조회 응답"""
    books: list[BookListItem]
    pagination: BookPagination
