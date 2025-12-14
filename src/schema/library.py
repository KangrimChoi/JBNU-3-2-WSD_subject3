"""Library Schemas"""
from datetime import datetime
from pydantic import BaseModel, Field


# ==================== Request Schemas ====================

class LibraryAddRequest(BaseModel):
    """라이브러리 도서 추가 요청"""
    bookId: int = Field(
        ...,
        json_schema_extra={"example": 1, "description": "추가할 도서 ID"}
    )


# ==================== Response Schemas ====================

class LibraryAddResponse(BaseModel):
    """라이브러리 도서 추가 응답"""
    bookId: int
    createdAt: datetime

    model_config = {"from_attributes": True}


class LibraryBookAuthor(BaseModel):
    """라이브러리 도서 저자 정보"""
    name: str


class LibraryBookInfo(BaseModel):
    """라이브러리 도서 정보"""
    id: int
    title: str
    author: LibraryBookAuthor
    isbn: str

    model_config = {"from_attributes": True}


class LibraryListItem(BaseModel):
    """라이브러리 목록 아이템"""
    book: LibraryBookInfo
    createdAt: datetime

    model_config = {"from_attributes": True}


class LibraryListResponse(BaseModel):
    """라이브러리 목록 조회 응답"""
    items: list[LibraryListItem]
