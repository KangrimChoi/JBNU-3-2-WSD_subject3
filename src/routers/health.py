from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("/")
async def health_check():
    """
    서버가 정상인지 확인
    """
    health_status = {
        "status": "OK",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "service": "WSD_Subject API Server",
        "developer": "202117643 최강림"
    }
    return health_status