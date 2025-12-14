#외부 모듈
from datetime import datetime
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

#내부 모듈
from src.database import get_db
from src.schema.comments import (
    CommentCreate,
    CommentCreateResponse
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
