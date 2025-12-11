#외부 모듈
from datetime import datetime
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import bcrypt

#내부 모듈
from src.database import get_db
from src.schema.users import UserCreate, UserCreateResponse, UserGetMeResponse
from src.schema.common import APIResponse, ErrorResponse
from src.models.user import User


router = APIRouter(prefix="/api/users", tags=["Users"])


def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# ==================== 유저 CRUD ====================

# Create (회원가입)
@router.post("/", summary="회원가입", response_model=APIResponse[UserCreateResponse], status_code=status.HTTP_201_CREATED)
async def create_user(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    """
    회원가입
    - 이메일 중복 검사
    - 비밀번호 bcrypt 해싱
    """
    # 이메일 중복 검사
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        error = ErrorResponse(
            timestamp=datetime.now(),
            path=str(request.url.path),
            status=409,
            code="DUPLICATE_EMAIL",
            message="이미 등록된 이메일입니다",
            details={"email": user.email}
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=error.model_dump(mode="json")
        )

    # 비밀번호 해싱 후 저장
    new_user = User(
        email=user.email,
        password_hash=hash_password(user.password),
        name=user.name,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return APIResponse(
        isSuccess=True,
        message="회원가입이 정상적으로 진행되었습니다.",
        payload=UserCreateResponse.model_validate(new_user)
    )


# Read (유저 정보 조회)

    
# Update (유저 정보 수정)

# Delete (유저 탈퇴)