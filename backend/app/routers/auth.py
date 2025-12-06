"""
Router de autenticación con JWT
Sistema completo de login, perfil y verificación
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from ..database import get_db
from ..schemas.user import LoginRequest, LoginResponse, UsuarioResponse, User
from ..security import (
    autenticar_usuario,
    crear_token,
    obtener_usuario_actual,
    verificar_rol
)

router = APIRouter()

# ============================================
# ENDPOINTS DE AUTENTICACIÓN
# ============================================

@router.post("/login", response_model=LoginResponse)
async def login(
    datos: LoginRequest,
    conn = Depends(get_db)
):
    """
    Iniciar sesión con username o email
    
    Returns:
        LoginResponse con token JWT y datos del usuario
    """
    # Autenticar usuario
    usuario = autenticar_usuario(
        conn, 
        datos.username_or_email, 
        datos.password
    )
    
    if not usuario:
        return LoginResponse(
            exito=False,
            mensaje="Credenciales incorrectas"
        )
    
    # Generar token JWT
    token = crear_token(usuario)
    
    # Preparar respuesta
    usuario_response = UsuarioResponse(
        id=usuario['id'],
        username=usuario['username'],
        email=usuario['email'],
        full_name=usuario.get('full_name'),
        role=usuario['role'],
        is_active=usuario['is_active']
    )
    
    return LoginResponse(
        exito=True,
        mensaje="Login exitoso",
        token=token,
        usuario=usuario_response
    )

@router.get("/perfil", response_model=User)
async def obtener_perfil(
    usuario = Depends(obtener_usuario_actual)
):
    """
    Obtener perfil del usuario autenticado
    
    Requiere: Token JWT válido en header Authorization
    """
    return User(
        id=usuario['id'],
        username=usuario['username'],
        email=usuario['email'],
        full_name=usuario.get('full_name'),
        role=usuario['role'],
        is_active=usuario['is_active'],
        created_at=usuario['created_at'],
        last_login=usuario.get('last_login')
    )

@router.get("/verificar")
async def verificar_token(
    usuario = Depends(obtener_usuario_actual)
):
    """
    Verificar si el token JWT es válido
    
    Returns:
        Dict con validez del token y datos del usuario
    """
    return {
        "valido": True,
        "usuario": {
            "id": usuario['id'],
            "username": usuario['username'],
            "email": usuario['email'],
            "full_name": usuario.get('full_name'),
            "role": usuario['role'],
            "is_active": usuario['is_active']
        }
    }

# ============================================
# ENDPOINT DE EJEMPLO: SOLO ADMIN
# ============================================

@router.get("/admin/test")
async def test_admin(
    usuario = Depends(verificar_rol("admin"))
):
    """
    Endpoint de prueba - solo usuarios con rol 'admin'
    """
    return {
        "mensaje": "Acceso autorizado",
        "usuario": usuario['username'],
        "rol": usuario['role']
    }
