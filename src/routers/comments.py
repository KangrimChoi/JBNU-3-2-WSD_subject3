#외부 모듈
import math
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload

#내부 모듈
from src.database import get_db
from src.schema.comments import (
    CommentCreate,
    CommentCreateResponse,
    CommentUpdate,
    CommentUpdateResponse,
    CommentAuthor,
    CommentListItem,
    CommentListResponse,
    CommentPagination
)
from src.schema.common import APIResponse, ErrorResponse
from src.models.comment import Comment
from src.models.book import Book
from src.models.user import User
from src.auth.jwt import get_current_user


router = APIRouter(prefix="/api", tags=["Comments"])

# ==================== 댓글 CRUD ====================

# Create (댓글 작성)
@router.post(
    "/books/{book_id}/comments",
    summary="댓글 작성",
    response_model=APIResponse[CommentCreateResponse],
    status_code=status.HTTP_201_CREATED
)
async def create_comment(
    request: Request,
    book_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    특정 도서에 대한 새 댓글을 작성합니다.
    - 인증 필요
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

    # 댓글 생성
    new_comment = Comment(
        user_id=current_user.id,
        book_id=book_id,
        content=comment_data.content
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return APIResponse(
        is_success=True,
        message="댓글이 성공적으로 작성되었습니다.",
        payload=CommentCreateResponse(
            id=new_comment.id,
            created_at=new_comment.created_at
        )
    )


# Read (댓글 목록 조회)
@router.get(
    "/books/{book_id}/comments",
    summary="댓글 목록 조회",
    response_model=APIResponse[CommentListResponse],
    status_code=status.HTTP_200_OK
)
async def get_comments(
    request: Request,
    book_id: int,
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    size: int = Query(10, ge=1, le=100, description="페이지당 댓글 수 (기본값: 10)"),
    db: Session = Depends(get_db)
):
    """
    특정 도서에 대한 댓글 목록을 페이지네이션으로 조회합니다.
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

    # 댓글 쿼리 (최신순 정렬)
    query = db.query(Comment).filter(
        Comment.book_id == book_id
    ).order_by(Comment.created_at.desc())

    # 전체 개수
    total_elements = query.count()
    total_pages = math.ceil(total_elements / size) if total_elements > 0 else 1

    # 페이지네이션 적용
    offset = (page - 1) * size
    comments = query.options(
        joinedload(Comment.user)
    ).offset(offset).limit(size).all()

    # 응답 생성
    comment_items = [
        CommentListItem(
            id=comment.id,
            author=CommentAuthor(name=comment.user.name),
            content=comment.content,
            created_at=comment.created_at
        )
        for comment in comments
    ]

    pagination = CommentPagination(
        page=page,
        totalPages=total_pages,
        totalElements=total_elements
    )

    return APIResponse(
        is_success=True,
        message="댓글 목록이 성공적으로 조회되었습니다.",
        payload=CommentListResponse(comments=comment_items, pagination=pagination)
    )


# Update (댓글 수정)
@router.patch(
    "/comments/{comment_id}",
    summary="댓글 수정",
    response_model=APIResponse[CommentUpdateResponse],
    status_code=status.HTTP_200_OK
)
async def update_comment(
    request: Request,
    comment_id: int,
    comment_data: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    본인이 작성한 댓글의 내용을 수정합니다.
    - 인증 필요
    - 본인 댓글만 수정 가능
    """
    # 댓글 조회
    comment = db.query(Comment).filter(Comment.id == comment_id).first()

    # 댓글 존재 여부 확인
    if not comment:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=404,
                code="COMMENT_NOT_FOUND",
                message="해당 댓글을 찾을 수 없습니다",
                details={"comment_id": comment_id}
            ).model_dump(mode="json")
        )

    # 본인 댓글인지 확인
    if comment.user_id != current_user.id:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=403,
                code="FORBIDDEN",
                message="본인의 댓글만 수정할 수 있습니다",
                details={"comment_id": comment_id}
            ).model_dump(mode="json")
        )

    # 필드 업데이트
    comment.content = comment_data.content
    comment.updated_at = datetime.now()

    db.commit()
    db.refresh(comment)

    return APIResponse(
        is_success=True,
        message="댓글이 성공적으로 수정되었습니다.",
        payload=CommentUpdateResponse(
            id=comment.id,
            updated_at=comment.updated_at
        )
    )
