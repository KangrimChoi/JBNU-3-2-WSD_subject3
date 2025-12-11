#환경 변수
from src.config import settings

#FastAPI
from fastapi import FastAPI
from src.routers import users, health

import uvicorn



## 서버실행
PORT_NUM = settings.PORT_NUM

tags_metadata = [
    {
        "name": "Users",
        "description": "사용자 관리 API",
    },
    {
        "name": "Health",
        "description": "서버 상태 확인 API",
    },
]

app = FastAPI(openapi_tags = tags_metadata)
app.include_router(users.router)
app.include_router(health.router)

@app.get("/")
async def root():
    return ("message: Server is running")

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=PORT_NUM, reload=True)
    