#외부 모듈
from datetime import datetime
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

#내부 모듈
from src.database import get_db
from sqlalchemy.orm import joinedload
from src.schema.library import (
    LibraryAddRequest,
    LibraryAddResponse,
    LibraryBookAuthor,
    LibraryBookInfo,
    LibraryListItem,
    LibraryListResponse,
    LibraryDeleteResponse
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
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "인증 필요"},
        404: {"model": ErrorResponse, "description": "도서를 찾을 수 없음"},
        409: {"model": ErrorResponse, "description": "이미 라이브러리에 추가됨 (중복)"},
        422: {"model": ErrorResponse, "description": "입력값 검증 실패"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    }
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


# Read (라이브러리 목록 조회)
@router.get(
    "/library",
    summary="라이브러리 목록 조회",
    response_model=APIResponse[LibraryListResponse],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "인증 필요"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    }
)
async def get_library(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    내 라이브러리 도서 목록을 조회합니다.
    - 인증 필요
    - 추가일 기준 최신순 정렬
    """
    # 라이브러리 아이템 조회 (도서 정보 포함)
    library_items = db.query(LibraryItem).filter(
        LibraryItem.user_id == current_user.id
    ).options(
        joinedload(LibraryItem.book).joinedload(Book.authors)
    ).order_by(LibraryItem.created_at.desc()).all()

    # 응답 생성
    items = []
    for item in library_items:
        book = item.book
        # 삭제된 도서는 제외
        if book and book.deleted_at is None:
            # 첫 번째 저자 이름 가져오기
            author_name = book.authors[0].name if book.authors else "Unknown"
            items.append(
                LibraryListItem(
                    book=LibraryBookInfo(
                        id=book.id,
                        title=book.title,
                        author=LibraryBookAuthor(name=author_name),
                        isbn=book.isbn
                    ),
                    createdAt=item.created_at
                )
            )

    return APIResponse(
        is_success=True,
        message="라이브러리 목록이 성공적으로 조회되었습니다.",
        payload=LibraryListResponse(items=items)
    )


# Delete (라이브러리 도서 삭제)
@router.delete(
    "/library/{book_id}",
    summary="라이브러리 도서 삭제",
    response_model=APIResponse[LibraryDeleteResponse],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "인증 필요"},
        404: {"model": ErrorResponse, "description": "라이브러리에 해당 도서 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    }
)
async def remove_from_library(
    request: Request,
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    내 라이브러리에서 도서를 삭제합니다.
    - 인증 필요
    - 본인 라이브러리의 도서만 삭제 가능
    """
    # 라이브러리 아이템 조회
    library_item = db.query(LibraryItem).filter(
        LibraryItem.user_id == current_user.id,
        LibraryItem.book_id == book_id
    ).first()

    # 라이브러리 아이템 존재 여부 확인
    if not library_item:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=404,
                code="LIBRARY_ITEM_NOT_FOUND",
                message="라이브러리에 해당 도서가 없습니다",
                details={"book_id": book_id}
            ).model_dump(mode="json")
        )

    # 라이브러리 아이템 삭제
    db.delete(library_item)
    db.commit()

    return APIResponse(
        is_success=True,
        message="라이브러리에서 도서가 삭제되었습니다.",
        payload=LibraryDeleteResponse(bookId=book_id)
    )
