"""
Utilidad para generar un hash bcrypt de una contraseña.

Uso:
    python generate_hash.py <contraseña>

Ejemplo:
    python generate_hash.py MiContraseñaSegura2024!

El hash resultante puede usarse para insertar usuarios directamente en la base de datos
o para verificar contraseñas manualmente.
"""
import sys
sys.path.append('/app')

from passlib.context import CryptContext

if len(sys.argv) != 2:
    print("Uso: python generate_hash.py <contraseña>")
    print("Ejemplo: python generate_hash.py MiContraseñaSegura2024!")
    sys.exit(1)

password = sys.argv[1]

if len(password) < 8:
    print("Advertencia: la contraseña tiene menos de 8 caracteres.")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash(password[:72])

print("Hash generado:")
print(hashed)
