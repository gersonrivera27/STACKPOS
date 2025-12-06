"""
Script de migración para crear tabla de usuarios
"""
import sys
import os
import psycopg2

def create_users_table():
    try:
        print("Conectando a la base de datos...")
        conn = psycopg2.connect(
            user="postgres",
            password="postgres",
            host="burger-db",
            port=5432,
            database="burger_pos"
        )
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
        
        print("Creando usuario admin por defecto...")
        # Hash generado con bcrypt 4.0.1 para 'admin123'
        hashed_password = "$2b$12$z/hT5aSEx5GEajsvaEEj3uiaD6TDSqbctokrrSZX7Q7d7E2Z209Pu"
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
    create_users_table()
