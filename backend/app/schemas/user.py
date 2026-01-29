from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
import re

# ============================================
# BASE SCHEMAS
# ============================================

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "staff"
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validar_password(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v

class User(UserBase):
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================
# AUTH REQUEST SCHEMAS
# ============================================

class LoginRequest(BaseModel):
    """Request body para login - acepta username o email"""
    username_or_email: str
    password: str
    
    @validator('username_or_email')
    def validar_username_or_email(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Username o email es requerido')
        return v.strip()

class PinLoginRequest(BaseModel):
    user_id: int
    pin: str

class UserLogin(BaseModel):
    """Schema legacy - mantener por compatibilidad"""
    username: str
    password: str

# ============================================
# AUTH RESPONSE SCHEMAS
# ============================================

class UsuarioResponse(BaseModel):
    """Información del usuario para incluir en responses"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    """Response completo del endpoint de login"""
    exito: bool
    mensaje: str
    token: Optional[str] = None
    usuario: Optional[UsuarioResponse] = None

class Token(BaseModel):
    """Schema legacy - mantener por compatibilidad"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema legacy - mantener por compatibilidad"""
    username: Optional[str] = None
