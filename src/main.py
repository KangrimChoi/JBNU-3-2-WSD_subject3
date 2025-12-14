#환경 변수
from src.config import settings

#FastAPI
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.routers import users, auth, books, health, reviews, comments, library, wishlist
from src.auth.jwt import APIException
from src.schema.common import ErrorResponse

#CORS
from fastapi.middleware.cors import CORSMiddleware

#레이트리밋
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import uvicorn



## 서버실행
PORT_NUM = settings.PORT_NUM

#레이트리밋 설정 (IP 기반, 분당 60회 기본 제한)
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

#API 문서 메타데이터
tags_metadata = [
    {
        "name": "Users",
        "description": "사용자 관리 API",
    },
    {
        "name": "Auth",
        "description": "인증 및 토큰 관리 API",
    },
    {
        "name": "Books",
        "description": "도서 관리 API",
    },
    
    {
        "name": "Reviews",
        "description": "리뷰 관리 API",
    },
    {
        "name": "Comments",
        "description": "댓글 관리 API",
    },
    {
        "name": "Library",
        "description": "내 라이브러리 관리 API",
    },
    {
        "name": "Wishlist",
        "description": "내 위시리스트 관리 API",
    },
    {
        "name": "Health",
        "description": "서버 상태 확인 API",
    },
]

#FastAPI 인스턴스 생성
app = FastAPI(openapi_tags = tags_metadata)

#CORS 설정 (테스트용 허용 도메인)
origins = [
    "http://localhost:3000",      # React 기본 포트
    "http://localhost:5173",      # Vite 기본 포트
    "http://localhost:5500",      # Live Server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # 허용할 도메인 목록
    allow_credentials=True,       # 쿠키 허용
    allow_methods=["*"],          # 모든 HTTP 메서드 허용
    allow_headers=["*"],          # 모든 헤더 허용
)

#레이트리밋 등록
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """레이트리밋 초과 시 ErrorResponse 형식으로 반환"""
    return JSONResponse(
        status_code=429,
        content=ErrorResponse(
            timestamp=datetime.now(),
            path=str(request.url.path),
            status=429,
            code="TOO_MANY_REQUESTS",
            message="요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.",
            details={"limit": str(exc.detail)}
        ).model_dump(mode="json")
    )

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(books.router)
app.include_router(reviews.router)
app.include_router(comments.router)
app.include_router(library.router)
app.include_router(wishlist.router)
app.include_router(health.router)

#전역 에러 처리
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """APIException을 ErrorResponse 형식으로 변환"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            timestamp=datetime.now(),
            path=str(request.url.path),
            status=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details
        ).model_dump(mode="json")
    )

#루트 엔드포인트
@app.get("/")
async def root():
    return ("message: Server is running")

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=PORT_NUM, reload=True)
    