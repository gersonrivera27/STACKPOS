"""
Router de autenticación con JWT
Sistema completo de login, perfil y verificación
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List

from ..database import get_db
from ..schemas.user import LoginRequest, LoginResponse, UsuarioResponse, User, PinLoginRequest
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

@router.get("/users-list", response_model=List[UsuarioResponse])
def listar_usuarios_login(conn = Depends(get_db)):
    """Listar usuarios activos para selector de login (PIN)"""
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, full_name, role, is_active FROM users WHERE is_active = TRUE ORDER BY full_name")
    users = cursor.fetchall()
    return [
        UsuarioResponse(
            id=u['id'], username=u['username'], email=u['email'],
            full_name=u['full_name'], role=u['role'], is_active=u['is_active']
        ) for u in users
    ]

@router.post("/pin-login", response_model=LoginResponse)
def login_con_pin(datos: PinLoginRequest, conn = Depends(get_db)):
    """Login usando PIN"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s AND pin = %s AND is_active = TRUE", (datos.user_id, datos.pin))
    usuario = cursor.fetchone()
    
    if not usuario:
        return LoginResponse(
            exito=False,
            mensaje="PIN incorrecto"
        )
        
    # Generar token
    token = crear_token(usuario)
    
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
