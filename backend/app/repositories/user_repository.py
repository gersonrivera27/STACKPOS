"""
Repositorio para usuarios
"""
from typing import Optional
from datetime import datetime
from ..schemas.user import UserCreate
from ..security import hashear_password

class UserRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_by_username(self, username: str) -> Optional[dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, username, email, hashed_password, full_name, role, is_active, created_at, last_login
            FROM users
            WHERE username = %s
        """, (username,))
        return cursor.fetchone()
    
    def get_by_email(self, email: str) -> Optional[dict]:
        """Buscar usuario por email"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, username, email, hashed_password, full_name, role, is_active, created_at, last_login
            FROM users
            WHERE email = %s
        """, (email,))
        return cursor.fetchone()
    
    def get_by_id(self, user_id: int) -> Optional[dict]:
        """Buscar usuario por ID"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, username, email, hashed_password, full_name, role, is_active, created_at, last_login
            FROM users
            WHERE id = %s
        """, (user_id,))
        return cursor.fetchone()
    
    def update_last_login(self, user_id: int) -> None:
        """Actualizar fecha de último acceso"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE users
            SET last_login = %s
            WHERE id = %s
        """, (datetime.utcnow(), user_id))
        self.conn.commit()

    def create(self, user: UserCreate) -> dict:
        cursor = self.conn.cursor()
        hashed_password = hashear_password(user.password)
        cursor.execute("""
            INSERT INTO users (username, email, hashed_password, full_name, role)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, username, email, full_name, role, is_active, created_at
        """, (user.username, user.email, hashed_password, user.full_name, user.role))
        return cursor.fetchone()
