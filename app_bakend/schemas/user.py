from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional
from datetime import datetime
import re


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        if len(v) > 72:
            raise ValueError('Password must be 72 characters or less')
        return v

    @validator('name')
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class Token(BaseModel):
    access_token: str
    token_type: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    credibility_score: int
    profile_image: Optional[str] = None

    class Config:
        from_attributes = True


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6, max_length=72)

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        if len(v) > 72:
            raise ValueError('Password must be 72 characters or less')
        return v


class UserProfileOut(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None
    role: str
    credibility_score: int
    profile_image: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    phone: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None
    name: Optional[str] = None