"""User Schemas"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


# ==================== Request Schemas ====================

class UserCreate(BaseModel):
    """회원가입 요청"""
    email: EmailStr = Field(..., json_schema_extra={"example": "user@example.com", "description": "사용자 이메일"})
    password: str = Field(..., min_length=8, max_length=100, json_schema_extra={"example": "P@ssw0rd!", "description": "사용자 비밀번호"})
    name: str = Field(..., min_length=2, max_length=100, json_schema_extra={"example": "홍길동", "description": "사용자 이름"})

# ==================== Response Schemas ====================
class UserCreateResponse(BaseModel):
    """사용자 응답 """
    id: int
    email: EmailStr
    name: str
    created_at: datetime
    
    model_config = {"from_attributes": True}
    
class UserGetMeResponse(BaseModel):
    """내 정보 조회 응답"""
    id: int
    email: EmailStr
    name: str
    role: str
    created_at: datetime
    
    model_config = {"from_attributes": True}