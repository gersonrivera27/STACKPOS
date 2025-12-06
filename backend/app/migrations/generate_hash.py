"""
Script para generar el hash correcto de la contraseña
"""
import sys
sys.path.append('/app')

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

password = "admin123"
hashed = pwd_context.hash(password[:72])

print(f"Hash generado para 'admin123':")
print(hashed)
