#외부 모듈
from datetime import datetime
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

#내부 모듈
from src.database import get_db
from src.schema.library import (
    LibraryAddRequest,
    LibraryAddResponse
)
from src.schema.common import APIResponse, ErrorResponse
from src.models.library_item import LibraryItem
from src.models.book import Book
from src.models.user import User
from src.auth.jwt import get_current_user


router = APIRouter(prefix="/api/me", tags=["Library"])

# ==================== 라이브러리 CRUD ====================

# Create (라이브러리 도서 추가)
@router.post(
    "/library",
    summary="라이브러리 도서 추가",
    response_model=APIResponse[LibraryAddResponse],
    status_code=status.HTTP_201_CREATED
)
async def add_to_library(
    request: Request,
    library_data: LibraryAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    내 라이브러리에 도서를 추가합니다.
    - 인증 필요
    - 중복 추가 불가
    """
    book_id = library_data.bookId

    # 도서 존재 여부 확인
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.deleted_at.is_(None)
    ).first()

    if not book:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=404,
                code="BOOK_NOT_FOUND",
                message="해당 도서를 찾을 수 없습니다",
                details={"book_id": book_id}
            ).model_dump(mode="json")
        )

    # 중복 추가 검사
    existing_item = db.query(LibraryItem).filter(
        LibraryItem.user_id == current_user.id,
        LibraryItem.book_id == book_id
    ).first()

    if existing_item:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=409,
                code="DUPLICATE_LIBRARY_ITEM",
                message="이미 라이브러리에 추가된 도서입니다",
                details={"book_id": book_id}
            ).model_dump(mode="json")
        )

    # 라이브러리 아이템 생성
    new_item = LibraryItem(
        user_id=current_user.id,
        book_id=book_id
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return APIResponse(
        is_success=True,
        message="라이브러리에 도서가 추가되었습니다.",
        payload=LibraryAddResponse(
            bookId=new_item.book_id,
            createdAt=new_item.created_at
        )
    )
