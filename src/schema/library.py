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
