"""
Router de autenticación con JWT
Sistema completo de login, perfil y verificación
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Annotated, List

from ..database import get_db
from ..schemas.user import LoginRequest, LoginResponse, UsuarioResponse, User, PinLoginRequest, RefreshTokenRequest
from ..security import (
    autenticar_usuario,
    crear_token,
    crear_refresh_token,
    decodificar_refresh_token,
    obtener_usuario_actual,
    verificar_rol,
    verificar_password
)
from ..core.rabbitmq import mq, get_client_ip
from ..core.rate_limiter import rate_limiter

router = APIRouter()

# ============================================
# ENDPOINTS DE AUTENTICACIÓN
# ============================================

@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    datos: LoginRequest,
    conn = Depends(get_db)
):
    """
    Iniciar sesion con username o email.
    Rate limited: 5 intentos por IP cada 15 min.
    Account lockout: 5 fallos bloquean la cuenta 15 min.
    """
    client_ip = get_client_ip(request)

    # Rate limit check (by IP)
    allowed, retry_after = rate_limiter.check_login_rate_limit(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos de login. Intente de nuevo en {retry_after} segundos.",
            headers={"Retry-After": str(retry_after)}
        )

    # Account lockout check
    locked, lock_retry = rate_limiter.is_account_locked(datos.username_or_email)
    if locked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Cuenta bloqueada temporalmente. Intente en {lock_retry} segundos.",
            headers={"Retry-After": str(lock_retry)}
        )

    # Record this attempt for rate limiting
    rate_limiter.record_login_attempt(client_ip)

    # Autenticar usuario
    usuario = autenticar_usuario(conn, datos.username_or_email, datos.password)

    if not usuario:
        # Record failed login for account lockout
        rate_limiter.record_failed_login(datos.username_or_email)

        await mq.publish_security_event(
            event="login_failed",
            username=datos.username_or_email,
            ip_address=client_ip,
            reason="Invalid credentials",
            severity="MEDIUM",
            metadata={
                "attempted_username": datos.username_or_email,
                "user_agent": request.headers.get('user-agent', 'Unknown')
            }
        )
        await mq.publish_auth_event(
            event="login_failed",
            username=datos.username_or_email,
            ip_address=client_ip,
            success=False,
            metadata={"reason": "Invalid credentials"}
        )

        return LoginResponse(
            exito=False,
            mensaje="Credenciales incorrectas"
        )

    # Clear lockout on successful login
    rate_limiter.clear_failed_logins(datos.username_or_email)

    await mq.publish_auth_event(
        event="login_success",
        username=usuario['username'],
        user_id=usuario['id'],
        ip_address=client_ip,
        success=True,
        metadata={"role": usuario['role']}
    )

    # Generar token JWT y refresh token
    token = crear_token(usuario)
    refresh_token = crear_refresh_token(usuario)

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
        refresh_token=refresh_token,
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
def listar_usuarios_login(
    conn = Depends(get_db),
    usuario = Depends(obtener_usuario_actual)
):
    """Listar usuarios activos. Requiere autenticación."""
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
async def login_con_pin(
    request: Request,
    datos: PinLoginRequest,
    conn = Depends(get_db)
):
    """
    Login usando PIN.
    Rate limited: 5 intentos por IP cada 15 min.
    """
    client_ip = get_client_ip(request)

    # Rate limit check
    allowed, retry_after = rate_limiter.check_login_rate_limit(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos. Intente en {retry_after} segundos.",
            headers={"Retry-After": str(retry_after)}
        )
    rate_limiter.record_login_attempt(client_ip)

    cursor = conn.cursor()
    # First find user by ID only
    cursor.execute("SELECT * FROM users WHERE id = %s AND is_active = TRUE", (datos.user_id,))
    usuario = cursor.fetchone()

    # Then verify PIN hash
    is_valid_pin = False
    if usuario and usuario.get('pin'):
        # For backwards compatibility during transition, we might have unhashed pins.
        # But we assume the hash_pins script runs correctly.
        pin_hash = usuario['pin']
        if str(pin_hash).startswith("$2"):
            is_valid_pin = verificar_password(datos.pin, pin_hash)
        else:
            # Fallback if somehow there's still a plaintext pin
            is_valid_pin = (datos.pin == pin_hash)

    if not usuario or not is_valid_pin:
        # Record failed PIN attempt for lockout
        rate_limiter.record_failed_login(f"pin_user_{datos.user_id}")

        await mq.publish_security_event(
            event="pin_login_failed",
            username=f"user_id_{datos.user_id}",
            ip_address=client_ip,
            reason="Invalid PIN or User not found",
            severity="MEDIUM",
            metadata={"user_id": datos.user_id}
        )

        return LoginResponse(
            exito=False,
            mensaje="PIN incorrecto"
        )

    # Clear lockout on success
    rate_limiter.clear_failed_logins(f"pin_user_{datos.user_id}")

    await mq.publish_auth_event(
        event="pin_login_success",
        username=usuario['username'],
        user_id=usuario['id'],
        ip_address=client_ip,
        success=True,
        metadata={"login_method": "PIN"}
    )

    # Generar tokens
    token = crear_token(usuario)
    refresh_token = crear_refresh_token(usuario)

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
        refresh_token=refresh_token,
        usuario=usuario_response
    )

# ============================================

@router.post("/refresh", response_model=LoginResponse)
async def refresh_access_token(
    datos: RefreshTokenRequest,
    conn = Depends(get_db)
):
    """
    Renovar access token usando un refresh token válido (7 días)
    """
    try:
        # Esto lanzará HTTPException si el token es inválido o no es tipo "refresh"
        payload = decodificar_refresh_token(datos.refresh_token)
        usuario_id = payload.get("usuario_id")
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s AND is_active = TRUE", (usuario_id,))
        usuario = cursor.fetchone()
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inactivo o no encontrado"
            )
            
        # Generar nuevos tokens (Access + Refresh) para mantener la sesión rotando
        token = crear_token(usuario)
        refresh_token = crear_refresh_token(usuario)
        
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
            mensaje="Token refrescado",
            token=token,
            refresh_token=refresh_token,
            usuario=usuario_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error al procesar el refresh token"
        )

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
