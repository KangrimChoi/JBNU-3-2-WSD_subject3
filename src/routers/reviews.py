#외부 모듈
import math
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

#내부 모듈
from src.database import get_db
from src.schema.reviews import (
    ReviewCreate,
    ReviewCreateResponse,
    ReviewUpdate,
    ReviewUpdateResponse,
    ReviewDeleteResponse,
    ReviewLikeResponse,
    ReviewAuthor,
    ReviewListItem,
    ReviewListResponse,
    ReviewPagination,
    TopReviewItem,
    TopReviewListResponse
)
from src.schema.common import APIResponse, ErrorResponse
from src.models.review import Review
from src.models.review_like import ReviewLike
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


# Read (리뷰 목록 조회)
@router.get(
    "/books/{book_id}/reviews",
    summary="리뷰 목록 조회",
    response_model=APIResponse[ReviewListResponse],
    status_code=status.HTTP_200_OK
)
async def get_reviews(
    request: Request,
    book_id: int,
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    size: int = Query(10, ge=1, le=100, description="페이지당 리뷰 수 (기본값: 10)"),
    db: Session = Depends(get_db)
):
    """
    특정 도서에 대한 리뷰 목록을 페이지네이션으로 조회합니다.
    - 인증 불필요
    - 삭제된 도서는 조회 불가
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

    # 리뷰 쿼리 (최신순 정렬)
    query = db.query(Review).filter(
        Review.book_id == book_id
    ).order_by(Review.created_at.desc())

    # 전체 개수
    total_elements = query.count()
    total_pages = math.ceil(total_elements / size) if total_elements > 0 else 1

    # 페이지네이션 적용
    offset = (page - 1) * size
    reviews = query.options(
        joinedload(Review.user)
    ).offset(offset).limit(size).all()

    # 응답 생성
    review_items = [
        ReviewListItem(
            id=review.id,
            author=ReviewAuthor(name=review.user.name),
            content=review.content,
            rating=review.rating,
            created_at=review.created_at
        )
        for review in reviews
    ]

    pagination = ReviewPagination(
        page=page,
        totalPages=total_pages,
        totalElements=total_elements
    )

    return APIResponse(
        is_success=True,
        message="리뷰 목록이 성공적으로 조회되었습니다.",
        payload=ReviewListResponse(reviews=review_items, pagination=pagination)
    )


# Update (리뷰 수정)
@router.patch(
    "/reviews/{review_id}",
    summary="리뷰 수정",
    response_model=APIResponse[ReviewUpdateResponse],
    status_code=status.HTTP_200_OK
)
async def update_review(
    request: Request,
    review_id: int,
    review_data: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    본인이 작성한 리뷰의 내용 또는 별점을 수정합니다.
    - 인증 필요
    - 본인 리뷰만 수정 가능
    """
    # 리뷰 조회
    review = db.query(Review).filter(Review.id == review_id).first()

    # 리뷰 존재 여부 확인
    if not review:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=404,
                code="REVIEW_NOT_FOUND",
                message="해당 리뷰를 찾을 수 없습니다",
                details={"review_id": review_id}
            ).model_dump(mode="json")
        )

    # 본인 리뷰인지 확인
    if review.user_id != current_user.id:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=403,
                code="FORBIDDEN",
                message="본인의 리뷰만 수정할 수 있습니다",
                details={"review_id": review_id}
            ).model_dump(mode="json")
        )

    # 필드 업데이트
    if review_data.content is not None:
        review.content = review_data.content
    if review_data.rating is not None:
        review.rating = review_data.rating

    review.updated_at = datetime.now()

    db.commit()
    db.refresh(review)

    return APIResponse(
        is_success=True,
        message="리뷰가 성공적으로 수정되었습니다.",
        payload=ReviewUpdateResponse(
            id=review.id,
            updated_at=review.updated_at
        )
    )


# Delete (리뷰 삭제)
@router.delete(
    "/reviews/{review_id}",
    summary="리뷰 삭제",
    response_model=APIResponse[ReviewDeleteResponse],
    status_code=status.HTTP_200_OK
)
async def delete_review(
    request: Request,
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    본인이 작성한 리뷰를 삭제합니다.
    - 인증 필요
    - 본인 리뷰만 삭제 가능
    """
    # 리뷰 조회
    review = db.query(Review).filter(Review.id == review_id).first()

    # 리뷰 존재 여부 확인
    if not review:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=404,
                code="REVIEW_NOT_FOUND",
                message="해당 리뷰를 찾을 수 없습니다",
                details={"review_id": review_id}
            ).model_dump(mode="json")
        )

    # 본인 리뷰인지 확인
    if review.user_id != current_user.id:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=403,
                code="FORBIDDEN",
                message="본인의 리뷰만 삭제할 수 있습니다",
                details={"review_id": review_id}
            ).model_dump(mode="json")
        )

    # 리뷰 ID 저장 (삭제 후 반환용)
    deleted_id = review.id

    # 리뷰 삭제
    db.delete(review)
    db.commit()

    return APIResponse(
        is_success=True,
        message="리뷰가 성공적으로 삭제되었습니다.",
        payload=ReviewDeleteResponse(id=deleted_id)
    )


# ==================== 리뷰 좋아요 ====================

# 리뷰 좋아요 등록
@router.post(
    "/reviews/{review_id}/like",
    summary="리뷰 좋아요",
    response_model=APIResponse[ReviewLikeResponse],
    status_code=status.HTTP_201_CREATED
)
async def like_review(
    request: Request,
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    리뷰에 좋아요를 등록합니다.
    - 인증 필요
    - 중복 좋아요 불가
    """
    review = db.query(Review).filter(Review.id == review_id).first()

    # 리뷰 존재 여부 확인
    if not review:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=404,
                code="REVIEW_NOT_FOUND",
                message="해당 리뷰를 찾을 수 없습니다",
                details={"review_id": review_id}
            ).model_dump(mode="json")
        )

    # 중복 좋아요 검사
    existing_like = db.query(ReviewLike).filter(
        ReviewLike.user_id == current_user.id,
        ReviewLike.review_id == review_id
    ).first()

    if existing_like:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=409,
                code="DUPLICATE_LIKE",
                message="이미 좋아요를 누른 리뷰입니다",
                details={"review_id": review_id}
            ).model_dump(mode="json")
        )

    # 좋아요 생성
    new_like = ReviewLike(
        user_id=current_user.id,
        review_id=review_id
    )

    db.add(new_like)
    db.commit()
    db.refresh(new_like)

    return APIResponse(
        is_success=True,
        message="좋아요가 등록되었습니다.",
        payload=ReviewLikeResponse(
            review_id=new_like.review_id,
            created_at=new_like.created_at
        )
    )


# 리뷰 좋아요 취소
@router.delete(
    "/reviews/{review_id}/like",
    summary="리뷰 좋아요 취소",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK
)
async def unlike_review(
    request: Request,
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    리뷰의 좋아요를 취소합니다.
    - 인증 필요
    - 본인이 누른 좋아요만 취소 가능
    """
    # 좋아요 조회
    like = db.query(ReviewLike).filter(
        ReviewLike.user_id == current_user.id,
        ReviewLike.review_id == review_id
    ).first()

    # 좋아요 존재 여부 확인
    if not like:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=404,
                code="LIKE_NOT_FOUND",
                message="좋아요를 누르지 않은 리뷰입니다",
                details={"review_id": review_id}
            ).model_dump(mode="json")
        )

    # 좋아요 삭제
    db.delete(like)
    db.commit()

    return APIResponse(
        is_success=True,
        message="좋아요가 취소되었습니다.",
        payload=None
    )


# ==================== Top-N 리뷰 ====================

@router.get(
    "/books/{book_id}/reviews/top",
    summary="Top-N 리뷰 목록 조회",
    response_model=APIResponse[TopReviewListResponse],
    status_code=status.HTTP_200_OK
)
async def get_top_reviews(
    request: Request,
    book_id: int,
    limit: int = Query(10, ge=1, le=50, description="조회할 리뷰 수 (기본값: 10, 최대: 50)"),
    db: Session = Depends(get_db)
):
    """
    특정 도서의 좋아요 순 Top-N 리뷰를 조회합니다.
    - 인증 불필요
    - 좋아요 수 기준 내림차순 정렬
    """
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.deleted_at.is_(None)
    ).first()

    # 도서 존재 여부 확인
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

    # 좋아요 수 기준 Top-N 리뷰 조회
    like_count = func.count(ReviewLike.review_id).label("like_count")

    reviews_with_likes = db.query(
        Review,
        like_count
    ).outerjoin(
        ReviewLike, Review.id == ReviewLike.review_id
    ).filter(
        Review.book_id == book_id
    ).group_by(
        Review.id
    ).order_by(
        like_count.desc(),
        Review.created_at.desc()
    ).limit(limit).all()

    # 응답 생성
    review_items = []
    for review, likes in reviews_with_likes:
        # user 정보 로드
        user = db.query(User).filter(User.id == review.user_id).first()
        review_items.append(
            TopReviewItem(
                id=review.id,
                author=ReviewAuthor(name=user.name if user else "Unknown"),
                content=review.content,
                rating=review.rating,
                like_count=likes or 0,
                created_at=review.created_at
            )
        )

    return APIResponse(
        is_success=True,
        message="Top 리뷰 목록이 성공적으로 조회되었습니다.",
        payload=TopReviewListResponse(reviews=review_items)
    )
