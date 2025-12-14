#환경 변수
from src.config import settings

#FastAPI
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.routers import users, auth, books, health, reviews
from src.auth.jwt import APIException
from src.schema.common import ErrorResponse

import uvicorn



## 서버실행
PORT_NUM = settings.PORT_NUM

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
        "name": "Health",
        "description": "서버 상태 확인 API",
    },
]

#FastAPI 인스턴스 생성
app = FastAPI(openapi_tags = tags_metadata)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(books.router)
app.include_router(reviews.router)
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
    