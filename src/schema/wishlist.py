"""Wishlist Schemas"""
from datetime import datetime
from pydantic import BaseModel, Field


# ==================== Request Schemas ====================

class WishlistAddRequest(BaseModel):
    """위시리스트 도서 추가 요청"""
    bookId: int = Field(
        ...,
        json_schema_extra={"example": 1, "description": "추가할 도서 ID"}
    )


# ==================== Response Schemas ====================

class WishlistAddResponse(BaseModel):
    """위시리스트 도서 추가 응답"""
    bookId: int
    createdAt: datetime

    model_config = {"from_attributes": True}

class WishlistBookAuthor(BaseModel):
    """위시리스트 도서 저자 정보"""
    name: str


class WishlistBookInfo(BaseModel):
    """위시리스트 도서 정보"""
    id: int
    title: str
    author: WishlistBookAuthor
    isbn: str

    model_config = {"from_attributes": True}


class WishlistListItem(BaseModel):
    """위시리스트 목록 아이템"""
    book: WishlistBookInfo
    createdAt: datetime

    model_config = {"from_attributes": True}


class WishlistListResponse(BaseModel):
    """위시리스트 목록 조회 응답"""
    items: list[WishlistListItem]



