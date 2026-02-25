"""
Router de autenticación con JWT
Sistema completo de login, perfil y verificación
"""
import hashlib
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List

from ..database import get_db
from ..schemas.user import (
    LoginRequest, LoginResponse, UsuarioResponse, User,
    PinLoginRequest, RefreshTokenRequest, LogoutRequest
)
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
from ..config import settings

router = APIRouter()


# ============================================
# HELPERS: Tabla refresh_tokens
# ============================================

def _hash_token(token: str) -> str:
    """SHA-256 del token JWT (no almacenamos el token completo)."""
    return hashlib.sha256(token.encode()).hexdigest()


def _store_refresh_token(conn, user_id: int, token: str) -> None:
    """Guarda el hash del refresh token en la tabla refresh_tokens."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
           VALUES (%s, %s, %s)""",
        (user_id, _hash_token(token), expires_at)
    )
    conn.commit()


def _revoke_refresh_token(conn, token: str) -> bool:
    """Marca el refresh token como revocado. Devuelve True si existía."""
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE refresh_tokens
           SET revoked_at = NOW()
           WHERE token_hash = %s AND revoked_at IS NULL""",
        (_hash_token(token),)
    )
    conn.commit()
    return cursor.rowcount > 0


def _is_refresh_token_valid(conn, token: str) -> bool:
    """Comprueba que el token existe, no está revocado y no ha expirado."""
    cursor = conn.cursor()
    cursor.execute(
        """SELECT 1 FROM refresh_tokens
           WHERE token_hash = %s
             AND revoked_at IS NULL
             AND expires_at > NOW()""",
        (_hash_token(token),)
    )
    return cursor.fetchone() is not None


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

    # Registrar refresh token en la base de datos para poder revocarlo
    _store_refresh_token(conn, usuario['id'], refresh_token)

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
    """Obtener perfil del usuario autenticado."""
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
    """Verificar si el token JWT es válido."""
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
    cursor.execute(
        "SELECT id, username, email, full_name, role, is_active FROM users WHERE is_active = TRUE ORDER BY full_name"
    )
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
    cursor.execute("SELECT * FROM users WHERE id = %s AND is_active = TRUE", (datos.user_id,))
    usuario = cursor.fetchone()

    # Verificar PIN hasheado con bcrypt
    is_valid_pin = False
    if usuario and usuario.get('pin'):
        pin_hash = usuario['pin']
        if str(pin_hash).startswith("$2"):
            is_valid_pin = verificar_password(datos.pin, pin_hash)

    if not usuario or not is_valid_pin:
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

    # Generar tokens y registrar refresh token en DB
    token = crear_token(usuario)
    refresh_token = crear_refresh_token(usuario)
    _store_refresh_token(conn, usuario['id'], refresh_token)

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


@router.post("/refresh", response_model=LoginResponse)
async def refresh_access_token(
    datos: RefreshTokenRequest,
    conn = Depends(get_db)
):
    """
    Renovar access token usando un refresh token válido.
    Verifica que el token no haya sido revocado (logout previo).
    Rota el refresh token: el anterior se revoca y se emite uno nuevo.
    """
    try:
        # Valida firma y expiración
        payload = decodificar_refresh_token(datos.refresh_token)
        usuario_id = payload.get("usuario_id")

        # Verificar que el token no fue revocado por logout
        if not _is_refresh_token_valid(conn, datos.refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revocado o no encontrado"
            )

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s AND is_active = TRUE", (usuario_id,))
        usuario = cursor.fetchone()

        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inactivo o no encontrado"
            )

        # Rotar: revocar el token usado y emitir uno nuevo
        _revoke_refresh_token(conn, datos.refresh_token)
        token = crear_token(usuario)
        refresh_token = crear_refresh_token(usuario)
        _store_refresh_token(conn, usuario['id'], refresh_token)

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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error al procesar el refresh token"
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    datos: LogoutRequest,
    conn = Depends(get_db),
    usuario = Depends(obtener_usuario_actual)
):
    """
    Cerrar sesión: revoca el refresh token en la base de datos.
    El access token expira solo (60 min), pero el refresh queda inválido
    de inmediato, impidiendo que se generen nuevos access tokens.
    """
    _revoke_refresh_token(conn, datos.refresh_token)

    await mq.publish_auth_event(
        event="logout",
        username=usuario['username'],
        user_id=usuario['id'],
        ip_address="unknown",
        success=True,
        metadata={}
    )


@router.get("/users-public")
def listar_usuarios_publico(conn = Depends(get_db)):
    """
    Lista mínima de usuarios activos para la pantalla de selección de PIN.
    Solo expone id y full_name. No requiere autenticación.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, full_name FROM users WHERE is_active = TRUE ORDER BY full_name"
    )
    users = cursor.fetchall()
    return [{"id": u["id"], "full_name": u["full_name"]} for u in users]
