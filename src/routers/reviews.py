#외부 모듈
from datetime import datetime
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

#내부 모듈
from src.database import get_db
from src.schema.reviews import ReviewCreate, ReviewCreateResponse
from src.schema.common import APIResponse, ErrorResponse
from src.models.review import Review
from src.models.book import Book
from src.models.user import User
from src.auth.jwt import get_current_user


router = APIRouter(prefix="/api", tags=["Reviews"])

# ==================== 리뷰 CRUD ====================

# Create (리뷰 작성)
@router.post(
    "/books/{book_id}/reviews",
    summary="리뷰 작성",
    response_model=APIResponse[ReviewCreateResponse],
    status_code=status.HTTP_201_CREATED
)
async def create_review(
    request: Request,
    book_id: int,
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    특정 도서에 대한 새 리뷰를 작성합니다.
    - 인증 필요
    - 한 사용자가 같은 도서에 중복 리뷰 불가
    """
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

    # 중복 리뷰 검사
    existing_review = db.query(Review).filter(
        Review.user_id == current_user.id,
        Review.book_id == book_id
    ).first()

    if existing_review:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=409,
                code="DUPLICATE_REVIEW",
                message="이미 해당 도서에 리뷰를 작성하셨습니다",
                details={"book_id": book_id}
            ).model_dump(mode="json")
        )

    # 리뷰 생성
    new_review = Review(
        user_id=current_user.id,
        book_id=book_id,
        content=review_data.content,
        rating=review_data.rating
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return APIResponse(
        is_success=True,
        message="리뷰가 성공적으로 작성되었습니다.",
        payload=ReviewCreateResponse(
            id=new_review.id,
            created_at=new_review.created_at
        )
    )
