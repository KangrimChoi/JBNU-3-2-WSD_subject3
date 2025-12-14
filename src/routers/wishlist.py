#외부 모듈
from datetime import datetime
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload

#내부 모듈
from src.database import get_db
from src.schema.wishlist import (
    WishlistAddRequest,
    WishlistAddResponse,
    WishlistBookAuthor,
    WishlistBookInfo,
    WishlistListItem,
    WishlistListResponse,
    WishlistDeleteResponse
)
from src.schema.common import APIResponse, ErrorResponse
from src.models.wishlist_item import WishlistItem
from src.models.book import Book
from src.models.user import User
from src.auth.jwt import get_current_user


router = APIRouter(prefix="/api/me", tags=["Wishlist"])

# ==================== 위시리스트 CRUD ====================

# Create (위시리스트 도서 추가)
@router.post(
    "/wishlist",
    summary="위시리스트 도서 추가",
    response_model=APIResponse[WishlistAddResponse],
    status_code=status.HTTP_201_CREATED
)
async def add_to_wishlist(
    request: Request,
    wishlist_data: WishlistAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    내 위시리스트에 도서를 추가합니다.
    - 인증 필요
    - 중복 추가 불가
    """
    book_id = wishlist_data.bookId

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
    existing_item = db.query(WishlistItem).filter(
        WishlistItem.user_id == current_user.id,
        WishlistItem.book_id == book_id
    ).first()

    if existing_item:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=409,
                code="DUPLICATE_WISHLIST_ITEM",
                message="이미 위시리스트에 추가된 도서입니다",
                details={"book_id": book_id}
            ).model_dump(mode="json")
        )

    # 위시리스트 아이템 생성
    new_item = WishlistItem(
        user_id=current_user.id,
        book_id=book_id
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return APIResponse(
        is_success=True,
        message="위시리스트에 도서가 추가되었습니다.",
        payload=WishlistAddResponse(
            bookId=new_item.book_id,
            createdAt=new_item.created_at
        )
    )


# Read (위시리스트 목록 조회)
@router.get(
    "/wishlist",
    summary="위시리스트 목록 조회",
    response_model=APIResponse[WishlistListResponse],
    status_code=status.HTTP_200_OK
)
async def get_wishlist(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    내 위시리스트 도서 목록을 조회합니다.
    - 인증 필요
    - 추가일 기준 최신순 정렬
    """
    # 위시리스트 아이템 조회 (도서 정보 포함)
    wishlist_items = db.query(WishlistItem).filter(
        WishlistItem.user_id == current_user.id
    ).options(
        joinedload(WishlistItem.book).joinedload(Book.authors)
    ).order_by(WishlistItem.created_at.desc()).all()

    # 응답 생성
    items = []
    for item in wishlist_items:
        book = item.book
        # 삭제된 도서는 제외
        if book and book.deleted_at is None:
            # 첫 번째 저자 이름 가져오기
            author_name = book.authors[0].name if book.authors else "Unknown"
            items.append(
                WishlistListItem(
                    book=WishlistBookInfo(
                        id=book.id,
                        title=book.title,
                        author=WishlistBookAuthor(name=author_name),
                        isbn=book.isbn
                    ),
                    createdAt=item.created_at
                )
            )

    return APIResponse(
        is_success=True,
        message="위시리스트 목록이 성공적으로 조회되었습니다.",
        payload=WishlistListResponse(items=items)
    )


