"""
Script de migración para crear tabla de usuarios y usuario administrador inicial.

Uso:
    python create_users.py <contraseña_admin>

Ejemplo:
    python create_users.py MiContraseñaSegura2024!

Requiere la variable de entorno DATABASE_URL configurada.
"""
import sys
import os
import psycopg2

def create_users_table(admin_password: str):
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Error: la variable de entorno DATABASE_URL no está definida.")
        sys.exit(1)

    # Importar aquí para no requerir passlib en entornos sin dependencias instaladas
    try:
        from passlib.context import CryptContext
    except ImportError:
        print("Error: passlib no está instalado. Ejecuta: pip install passlib[bcrypt]")
        sys.exit(1)

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(admin_password[:72])

    try:
        print("Conectando a la base de datos...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        print("Recreando tabla users...")
        # DROP TABLE para asegurar esquema limpio
        cursor.execute("DROP TABLE IF EXISTS users CASCADE")

        cursor.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                hashed_password VARCHAR(200) NOT NULL,
                full_name VARCHAR(100),
                role VARCHAR(20) DEFAULT 'staff',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)

        # Crear índice
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")

        print("Creando usuario admin...")
        cursor.execute("""
            INSERT INTO users (username, email, hashed_password, full_name, role)
            VALUES (%s, %s, %s, %s, %s)
        """, ('admin', 'admin@burgerpos.com', hashed_password, 'System Admin', 'admin'))

        conn.commit()
        cursor.close()
        conn.close()
        print("Migración completada exitosamente.")

    except Exception as e:
        print(f"Error en migración: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python create_users.py <contraseña_admin>")
        print("Ejemplo: python create_users.py MiContraseñaSegura2024!")
        sys.exit(1)

    password_arg = sys.argv[1]
    if len(password_arg) < 8:
        print("Error: la contraseña debe tener al menos 8 caracteres.")
        sys.exit(1)

    create_users_table(password_arg)
