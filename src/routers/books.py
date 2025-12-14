#외부 모듈
import math
from datetime import datetime
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload

#내부 모듈
from src.database import get_db
from src.schema.books import (
    BookCreate,
    BookCreateResponse,
    BookListItem,
    BookListResponse,
    BookPagination
)
from src.schema.common import APIResponse, ErrorResponse
from src.models.book import Book
from src.models.author import Author
from src.models.category import Category
from src.auth.jwt import get_current_admin_user
from src.models.user import User


router = APIRouter(prefix="/api/books", tags=["Books"])

# ==================== 도서 CRUD ====================

# Create (도서 등록) - 관리자 전용
@router.post(
    "/",
    summary="도서 등록 (관리자)",
    response_model=APIResponse[BookCreateResponse],
    status_code=status.HTTP_201_CREATED
)
async def create_book(
    request: Request,
    book_data: BookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    새로운 도서를 등록합니다.
    - 관리자 권한 필요
    - ISBN 중복 검사
    - 저자/카테고리가 없으면 자동 생성
    """
    # ISBN 중복 검사
    existing_book = db.query(Book).filter(Book.isbn == book_data.isbn).first()
    if existing_book:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=409,
                code="DUPLICATE_ISBN",
                message="이미 등록된 ISBN입니다",
                details={"isbn": book_data.isbn}
            ).model_dump(mode="json")
        )

    # 저자 처리 (없으면 생성)
    authors = []
    for author_name in book_data.authors:
        author = db.query(Author).filter(Author.name == author_name).first()
        if not author:
            author = Author(name=author_name)
            db.add(author)
            db.flush()  # ID 할당을 위해 flush
        authors.append(author)

    # 카테고리 처리 (없으면 생성)
    categories = []
    for category_name in book_data.categories:
        category = db.query(Category).filter(Category.name == category_name).first()
        if not category:
            category = Category(name=category_name)
            db.add(category)
            db.flush()
        categories.append(category)

    # 도서 생성
    new_book = Book(
        title=book_data.title,
        description=book_data.description,
        isbn=book_data.isbn,
        cover_image_url=book_data.cover_image_url,
        price=book_data.price,
        publication_date=book_data.publication_date
    )
    new_book.authors = authors
    new_book.categories = categories

    db.add(new_book)
    db.commit()
    db.refresh(new_book)

    # 응답 생성
    response_data = BookCreateResponse(
        id=new_book.id,
        title=new_book.title,
        categories=[cat.name for cat in new_book.categories],
        authors=[auth.name for auth in new_book.authors],
        description=new_book.description,
        isbn=new_book.isbn,
        cover_image_url=new_book.cover_image_url,
        price=new_book.price,
        publication_date=new_book.publication_date,
        created_at=new_book.created_at
    )

    return APIResponse(
        is_success=True,
        message="도서가 성공적으로 등록되었습니다.",
        payload=response_data
    )


# Read (도서 목록 조회) - 페이지네이션
@router.get(
    "/",
    summary="도서 목록 조회",
    response_model=APIResponse[BookListResponse],
    status_code=status.HTTP_200_OK
)
async def get_books(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    sort_by: int = Query(0, ge=0, le=1, description="정렬 기준 (0: 내림차순, 1: 오름차순)"),
    db: Session = Depends(get_db)
):
    """
    도서 목록을 페이지네이션하여 조회합니다.
    - 인증 불필요
    - 삭제된 도서 제외 (soft delete)
    - 카테고리 필터링 지원
    - 정렬: 0=내림차순(최신순), 1=오름차순(오래된순)
    """
    # 기본 쿼리 (삭제되지 않은 도서만)
    query = db.query(Book).filter(Book.deleted_at.is_(None))

    # 카테고리 필터
    if category:
        query = query.join(Book.categories).filter(Category.name == category)

    # 정렬
    if sort_by == 1:
        query = query.order_by(Book.created_at.asc())
    else:
        query = query.order_by(Book.created_at.desc())

    # 전체 개수
    total_books = query.count()
    total_pages = math.ceil(total_books / limit) if total_books > 0 else 1

    # 페이지네이션 적용
    offset = (page - 1) * limit
    books = query.options(
        joinedload(Book.authors),
        joinedload(Book.categories)
    ).offset(offset).limit(limit).all()

    # 응답 생성
    book_items = [
        BookListItem(
            id=book.id,
            title=book.title,
            categories=[cat.name for cat in book.categories],
            authors=[auth.name for auth in book.authors],
            description=book.description,
            isbn=book.isbn,
            cover_image_url=book.cover_image_url,
            price=book.price,
            publication_date=book.publication_date
        )
        for book in books
    ]

    pagination = BookPagination(
        total_books=total_books,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
        page_sort=sort_by
    )

    return APIResponse(
        is_success=True,
        message="도서 목록 조회에 성공했습니다.",
        payload=BookListResponse(books=book_items, pagination=pagination)
    )
