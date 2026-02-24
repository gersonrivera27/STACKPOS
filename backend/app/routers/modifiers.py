"""
Router para gestión de modificadores
"""
from fastapi import APIRouter, HTTPException, Depends, status
from ..security import obtener_usuario_actual, verificar_rol
from typing import List
import psycopg2

from ..database import get_db
from ..models import Modifier, ModifierCreate

router = APIRouter()

@router.get("", response_model=List[Modifier])
def get_modifiers(conn = Depends(get_db), usuario = Depends(obtener_usuario_actual)):
    """Obtener todos los modificadores"""
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, is_active FROM modifiers ORDER BY name")
    modifiers = cursor.fetchall()
    return modifiers

@router.post("", response_model=Modifier, status_code=status.HTTP_201_CREATED)
def create_modifier(modifier: ModifierCreate, conn = Depends(get_db), usuario = Depends(verificar_rol("admin"))):
    """Crear un nuevo modificador"""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO modifiers (name, price) VALUES (%s, %s) RETURNING id, name, price, is_active",
        (modifier.name, modifier.price)
    )
    new_modifier = cursor.fetchone()
    conn.commit()
    return new_modifier
