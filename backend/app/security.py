"""
Utilidades de seguridad (Hashing y JWT)
Sistema completo de autenticación JWT
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer
from typing import Annotated

from .config import settings
from .database import get_db

# CONFIGURACIÓN
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# ============================================
# FUNCIONES DE PASSWORD
# ============================================

def hashear_password(password: str) -> str:
    """Hashear password con bcrypt"""
    # Truncar a 72 bytes para cumplir con la limitación de bcrypt
    return pwd_context.hash(password[:72])

def verificar_password(password_plano: str, password_hash: str) -> bool:
    """Verificar password contra hash"""
    # Truncar a 72 bytes para cumplir con la limitación de bcrypt
    return pwd_context.verify(password_plano[:72], password_hash)

# ============================================
# FUNCIONES JWT
# ============================================

def crear_token(usuario: dict) -> str:
    """
    Crear JWT access token. Duración configurable via ACCESS_TOKEN_EXPIRE_MINUTES (default 60 min).
    """
    now = datetime.now(timezone.utc)
    expiracion = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": str(usuario['id']),
        "usuario_id": usuario['id'],
        "username": usuario['username'],
        "email": usuario['email'],
        "rol": usuario['role'],
        "type": "access",
        "exp": expiracion,
        "iat": now
    }
    
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def crear_refresh_token(usuario: dict) -> str:
    """
    Crear JWT refresh token. Duración configurable via REFRESH_TOKEN_EXPIRE_DAYS (default 7 días).
    """
    now = datetime.now(timezone.utc)
    expiracion = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": str(usuario['id']),
        "usuario_id": usuario['id'],
        "type": "refresh",
        "exp": expiracion,
        "iat": now
    }
    
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decodificar_refresh_token(token: str) -> Dict[str, Any]:
    """
    Decodificar y validar refresh token.
    Raises HTTPException if token is invalid, expired, or not a refresh token.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalido: no es un refresh token"
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

def decodificar_token(token: str) -> Dict[str, Any]:
    """
    Decodificar y validar JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Dict con el payload del token
    
    Raises:
        HTTPException: Si el token es inválido o expirado
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        # Rechazar refresh tokens usados como access tokens
        if payload.get("type") == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: se requiere access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ============================================
# DEPENDENCIAS FASTAPI
# ============================================

async def obtener_usuario_actual(
    token: Annotated[str, Depends(security)],
    conn = Depends(get_db)
):
    """
    Dependency para obtener el usuario autenticado actual
    
    Uso en rutas:
        async def mi_ruta(usuario = Depends(obtener_usuario_actual)):
            # usuario contiene los datos del usuario autenticado
    
    Returns:
        Dict con datos del usuario autenticado
    
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta token de autenticación",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Extraer token del header Bearer
    token_str = token.credentials if hasattr(token, 'credentials') else token
    
    # Decodificar token
    payload = decodificar_token(token_str)
    
    usuario_id = payload.get("usuario_id")
    if not usuario_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: falta usuario_id"
        )
    
    # Buscar usuario en base de datos
    from .repositories.user_repository import UserRepository
    repo = UserRepository(conn)
    usuario = repo.get_by_id(usuario_id)
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )
    
    if not usuario.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo"
        )
    
    # Agregar payload del token al usuario para fácil acceso
    usuario['token_payload'] = payload
    
    return usuario

def verificar_rol(*roles_permitidos: str):
    """
    Dependency para verificar roles de usuario
    
    Uso en rutas:
        @router.get("/admin")
        async def ruta_admin(usuario = Depends(verificar_rol("admin"))):
            # Solo usuarios con rol "admin" pueden acceder
    
        @router.get("/reportes")
        async def reportes(usuario = Depends(verificar_rol("admin", "manager"))):
            # Usuarios con rol "admin" o "manager" pueden acceder
    
    Args:
        *roles_permitidos: Roles que tienen permiso para acceder
    
    Returns:
        Dependency function que valida el rol
    """
    async def verificador(usuario = Depends(obtener_usuario_actual)):
        rol_usuario = usuario.get('role', '')
        if rol_usuario not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere uno de estos roles: {', '.join(roles_permitidos)}"
            )
        return usuario
    return verificador

# ============================================
# FUNCIONES HELPER
# ============================================

def autenticar_usuario(conn, username_or_email: str, password: str) -> Optional[dict]:
    """
    Autenticar usuario por username o email
    
    Args:
        conn: Conexión a base de datos
        username_or_email: Username o email del usuario
        password: Password en texto plano
    
    Returns:
        Dict con datos del usuario si la autenticación es exitosa, None si falla
    """
    from .repositories.user_repository import UserRepository
    repo = UserRepository(conn)
    
    # Intentar buscar por username primero
    usuario = repo.get_by_username(username_or_email)
    
    # Si no se encuentra, intentar por email
    if not usuario:
        usuario = repo.get_by_email(username_or_email)
    
    # Si no existe el usuario o la contraseña es incorrecta
    if not usuario or not verificar_password(password, usuario['hashed_password']):
        return None
    
    # Verificar que el usuario esté activo
    if not usuario.get('is_active', True):
        return None
    
    # Actualizar último acceso
    repo.update_last_login(usuario['id'])
    
    return usuario

