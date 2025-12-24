#외부 모듈
from datetime import datetime
import secrets
from fastapi import APIRouter, status, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session


#내부 모듈
from src.schema.auth import AuthLogin, LoginResponse, TokenRefresh, TokenRefreshResponse
from src.schema.common import APIResponse, ErrorResponse
from src.database import get_db
from src.models.user import User
from src.config import settings
from src.auth.jwt import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
)
from src.auth.password import verify_password, hash_password
from src.auth.oauth import get_google_oauth_client
from src.redis import (
    store_refresh_token,
    is_valid_refresh_token,
    delete_refresh_token,
    blacklist_access_token,
)


security = HTTPBearer()


router = APIRouter(prefix="/api/auth", tags=["Auth"])


# ==================== 인증 및 토큰 관리 ====================

# 로그인
@router.post(
    "/login",
    summary="로그인",
    response_model=APIResponse[LoginResponse],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "이메일 또는 비밀번호 불일치"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    }
)
def login(request: Request, user_credentials: AuthLogin, db: Session = Depends(get_db)):
    """사용자 로그인 및 JWT 토큰 발급"""
    # 사용자 조회
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=401,
                code="UNAUTHORIZED",
                message="Invalid email or password"
            ).model_dump(mode="json")
        )

    # 비밀번호 검증
    if not verify_password(user_credentials.password, str(user.password_hash)):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=401,
                code="UNAUTHORIZED",
                message="Invalid email or password"
            ).model_dump(mode="json")
        )

    # JWT 토큰 생성
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    # Refresh Token을 Redis에 저장
    refresh_expires_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    store_refresh_token(user.id, refresh_token, refresh_expires_seconds)

    return APIResponse(
        is_success=True,
        message="로그인 성공",
        payload=LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    )


# 토큰 갱신
@router.post(
    "/refresh",
    summary="토큰 갱신",
    response_model=APIResponse[TokenRefreshResponse],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "유효하지 않거나 만료된 Refresh Token"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    }
)
def refresh_token_endpoint(request: Request, token_request: TokenRefresh, db: Session = Depends(get_db)):
    """Refresh Token으로 새로운 Access Token 발급"""
    # Refresh Token 검증
    payload = verify_token(token_request.refresh_token, token_type="refresh")

    # 사용자 존재 확인
    user_id = payload.get("sub")
    if user_id is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=401,
                code="UNAUTHORIZED",
                message="Invalid token payload"
            ).model_dump(mode="json")
        )
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=401,
                code="USER_NOT_FOUND",
                message="User not found"
            ).model_dump(mode="json")
        )

    # Redis에서 Refresh Token 유효성 확인
    if not is_valid_refresh_token(int(user_id), token_request.refresh_token):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=401,
                code="INVALID_REFRESH_TOKEN",
                message="Refresh token is invalid or expired"
            ).model_dump(mode="json")
        )

    # 새 Access Token 발급
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    new_access_token = create_access_token(data=token_data)

    return APIResponse(
        is_success=True,
        message="토큰 갱신 성공",
        payload=TokenRefreshResponse(
            access_token=new_access_token,
            token_type="bearer"
        )
    )


# 로그아웃
@router.post(
    "/logout",
    summary="로그아웃",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "인증 필요 (유효하지 않은 토큰)"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    }
)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user)
):
    """
    로그아웃 처리
    - Access Token을 블랙리스트에 추가
    - Refresh Token을 Redis에서 삭제
    """
    # Access Token 블랙리스트에 추가
    access_token = credentials.credentials
    access_expires_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    blacklist_access_token(access_token, access_expires_seconds)

    # Refresh Token 삭제
    delete_refresh_token(current_user.id)

    return APIResponse(
        is_success=True,
        message="로그아웃 성공",
        payload=None
    )

# ==================== 소셜 로그인 (Google OAuth 2.0) ====================

# Google 로그인 리다이렉트
@router.get(
    "/google",
    summary="Google 소셜 로그인",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    responses={
        307: {"description": "Google 로그인 페이지로 리다이렉트"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    }
)
async def google_login(request: Request):
    """
    Google OAuth 2.0 로그인 페이지로 리다이렉트
    - 사용자를 Google 인증 페이지로 보냄
    """
    google = get_google_oauth_client()
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    response = await google.authorize_redirect(request, redirect_uri)
    response.status_code = 307
    return response


# Google 콜백 처리
@router.get(
    "/google/callback",
    summary="Google 소셜 로그인 콜백",
    response_model=APIResponse[LoginResponse],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Google 인증 실패"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    }
)
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Google OAuth 2.0 콜백 처리
    - Google로부터 인증 코드를 받아 액세스 토큰 교환
    - 사용자 정보 조회 후 회원가입 또는 로그인 처리
    - JWT 토큰 발급
    """
    try:
        # Google OAuth 토큰 교환
        google = get_google_oauth_client()
        token = await google.authorize_access_token(request)
        
        # 사용자 정보 가져오기
        user_info = token.get('userinfo')
        if not user_info:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=ErrorResponse(
                    timestamp=datetime.now(),
                    path=str(request.url.path),
                    status=401,
                    code="UNAUTHORIZED",
                    message="Failed to retrieve user information from Google"
                ).model_dump(mode="json")
            )
            
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0])
        
        # 기존 사용자 조회
        user = db.query(User).filter(User.email == email).first()
        
        # 신규 사용자인 경우 자동 회원가입
        if not user:
            # 임시 랜덤 비밀번호 생성 (소셜 로그인 사용자는 이 비밀번호를 알 수 없음)
            random_password = secrets.token_urlsafe(32)
            hashed_password = hash_password(random_password)
            
            user = User(
                email=email,
                name=name,
                password_hash=hashed_password,
                role="user"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
        # JWT 토큰 생성
        token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)
        
        # Refresh Token을 Redis에 저장
        refresh_expires_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        store_refresh_token(user.id, refresh_token, refresh_expires_seconds)
        
        return APIResponse(
            is_success=True,
            message="Google 로그인 성공",
            payload=LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer"
            )
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                timestamp=datetime.now(),
                path=str(request.url.path),
                status=500,
                code="INTERNAL_SERVER_ERROR",
                message=f"Google authentication failed: {str(e)}"
            ).model_dump(mode="json")
        )
