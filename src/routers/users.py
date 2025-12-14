#외부 모듈
from datetime import datetime
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import bcrypt

#내부 모듈
from src.database import get_db
from src.schema.users import UserCreate, UserCreateResponse, UserGetMeResponse, UserUpdate
from src.schema.common import APIResponse, ErrorResponse
from src.models.user import User
from src.auth.password import hash_password, verify_password
from src.auth.jwt import get_current_user, get_current_admin_user


router = APIRouter(prefix="/api/users", tags=["Users"])

# ==================== 유저 CRUD ====================

# Create (회원가입)
@router.post(
    "/",
    summary="회원가입",
    response_model=APIResponse[UserCreateResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "이메일 중복"},
        422: {"model": ErrorResponse, "description": "입력값 검증 실패"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    }
)
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
        is_success=True,
        message="회원가입이 정상적으로 진행되었습니다.",
        payload=UserCreateResponse.model_validate(new_user)
    )


# Read (유저 정보 조회)

# 내 정보 조회
@router.get(
    "/me",
    summary="내 정보 조회",
    response_model=APIResponse[UserGetMeResponse],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "인증 필요"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    }
)
def get_me(current_user: User = Depends(get_current_user)):
    """
    현재 로그인한 사용자의 프로필 정보를 조회합니다.
    - 인증 필요 (Bearer Token)
    """
    return APIResponse(
        is_success=True,
        message="프로필 조회 성공",
        payload=UserGetMeResponse.model_validate(current_user)
    )


# 사용자 목록 조회 (ADMIN)
@router.get(
    "/",
    summary="사용자 목록 조회 (ADMIN)",
    response_model=APIResponse[list[UserGetMeResponse]],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "인증 필요"},
        403: {"model": ErrorResponse, "description": "관리자 권한 필요"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    }
)
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    모든 사용자 목록을 조회합니다.
    - 관리자 전용 API
    - 관리자 계정은 목록에서 제외됩니다.
    """
    users = db.query(User).filter(User.role != "admin").all()
    return APIResponse(
        is_success=True,
        message="사용자 목록 조회 성공",
        payload=[UserGetMeResponse.model_validate(user) for user in users]
    )


# 특정 사용자 조회 (ADMIN)
@router.get(
    "/{user_id}",
    summary="특정 사용자 조회 (ADMIN)",
    response_model=APIResponse[UserGetMeResponse],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "인증 필요"},
        403: {"model": ErrorResponse, "description": "관리자 권한 필요"},
        404: {"model": ErrorResponse, "description": "사용자를 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    }
)
def get_user_by_id(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    특정 사용자의 정보를 조회합니다.
    - 관리자 전용 API
    - 관리자 계정은 조회할 수 없습니다.
    """
    user = db.query(User).filter(User.id == user_id, User.role != "admin").first()
    if not user:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=404,
                code="USER_NOT_FOUND",
                message="사용자를 찾을 수 없습니다",
                details={"user_id": user_id}
            ).model_dump(mode="json")
        )

    return APIResponse(
        is_success=True,
        message="사용자 조회 성공",
        payload=UserGetMeResponse.model_validate(user)
    )


# Update (유저 정보 수정)

# 내 정보 수정
@router.patch(
    "/me",
    summary="내 정보 수정",
    response_model=APIResponse[UserGetMeResponse],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청 (수정 내용 없음)"},
        401: {"model": ErrorResponse, "description": "인증 필요 또는 현재 비밀번호 불일치"},
        403: {"model": ErrorResponse, "description": "관리자 계정 수정 불가"},
        422: {"model": ErrorResponse, "description": "입력값 검증 실패"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    }
)
def update_me(
    request: Request,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    현재 로그인한 사용자의 정보를 수정합니다.
    - 이름 변경: name 필드만 전송
    - 비밀번호 변경: current_password와 new_password 모두 필요
    - 관리자 계정은 API를 통한 수정이 불가합니다.
    """
    # 관리자 계정 수정 차단
    if str(current_user.role) == "admin":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=403,
                code="FORBIDDEN",
                message="관리자 계정은 API를 통해 수정할 수 없습니다"
            ).model_dump(mode="json")
        )

    # 수정할 내용이 없는 경우
    if not user_update.name and not user_update.new_password:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=400,
                code="BAD_REQUEST",
                message="수정할 내용이 없습니다"
            ).model_dump(mode="json")
        )

    # 비밀번호 변경 요청인 경우
    if user_update.new_password:
        # 현재 비밀번호 필수 확인
        if not user_update.current_password:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    timestamp=datetime.now(),
                    path=str(request.url.path),
                    status=400,
                    code="VALIDATION_FAILED",
                    message="비밀번호 변경 시 현재 비밀번호가 필요합니다",
                    details={"current_password": "현재 비밀번호를 입력해주세요"}
                ).model_dump(mode="json")
            )

        # 현재 비밀번호 검증
        if not verify_password(user_update.current_password, str(current_user.password_hash)):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=ErrorResponse(
                    timestamp=datetime.now(),
                    path=str(request.url.path),
                    status=401,
                    code="UNAUTHORIZED",
                    message="현재 비밀번호가 일치하지 않습니다"
                ).model_dump(mode="json")
            )

        # 새 비밀번호로 변경
        current_user.password_hash = hash_password(user_update.new_password)

    # 이름 변경
    if user_update.name:
        current_user.name = user_update.name

    db.commit()
    db.refresh(current_user)

    return APIResponse(
        is_success=True,
        message="프로필 수정 성공",
        payload=UserGetMeResponse.model_validate(current_user)
    )


# Delete (유저 탈퇴)

# 회원 탈퇴
@router.delete(
    "/me",
    summary="회원 탈퇴",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "인증 필요"},
        403: {"model": ErrorResponse, "description": "관리자 계정 삭제 불가"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    }
)
def delete_me(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    현재 로그인한 사용자의 계정을 삭제합니다.
    - 관리자 계정은 API를 통한 삭제가 불가합니다.
    """
    # 관리자 계정 삭제 차단
    if str(current_user.role) == "admin":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=403,
                code="FORBIDDEN",
                message="관리자 계정은 API를 통해 삭제할 수 없습니다"
            ).model_dump(mode="json")
        )

    db.delete(current_user)
    db.commit()

    return APIResponse(
        is_success=True,
        message="회원 탈퇴가 완료되었습니다",
        payload=None
    )