from fastapi import APIRouter, HTTPException, Depends, status
from ..security import obtener_usuario_actual, verificar_rol
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import psycopg2

from ..database import get_db
from ..models.table import Table, TableCreate, ActiveOrderInfo

router = APIRouter()

@router.get("", response_model=List[Table])
def get_tables(conn = Depends(get_db), usuario = Depends(obtener_usuario_actual)):
    """Obtener todas las mesas con información de ocupación"""
    cursor = conn.cursor()
    
    # Query join tables with their ACTIVE order (not completed/cancelled)
    # Seleccionamos la orden más reciente que esté activa para esa mesa
    query = """
        SELECT 
            t.id, t.table_number, t.is_occupied, t.x, t.y,
            o.id as order_id, o.customer_name, o.total, o.created_at as order_created_at
        FROM tables t
        LEFT JOIN orders o ON o.table_id = t.id 
             AND o.status NOT IN ('completed', 'cancelled')
        ORDER BY t.table_number
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    tables_result = []
    for row in rows:
        # Check if we have an active order for this table
        
        active_order = None
        if row['order_id']:
            # Calculate elapsed time string
            diff = datetime.now() - row['order_created_at']
            if diff.total_seconds() < 3600:
                elapsed = f"{int(diff.total_seconds() // 60)} Mins"
            else:
                elapsed = f"{int(diff.total_seconds() // 3600)}h {int((diff.total_seconds() % 3600) // 60)}m"

            active_order = ActiveOrderInfo(
                id=row['order_id'],
                customer_name=row['customer_name'] or "Cliente",
                total=row['total'] or Decimal(0),
                created_at=row['order_created_at'],
                time_elapsed=elapsed
            )

        tables_result.append(Table(
            id=row['id'],
            table_number=row['table_number'],
            is_occupied=row['is_occupied'],
            x=row['x'] or 0,
            y=row['y'] or 0,
            active_order=active_order
        ))
    
    # Remove duplicates if any (due to join) - simplified approach
    # Ideally use DISTINCT ON or group by
    unique_tables = {t.id: t for t in tables_result}.values()
    
    return list(unique_tables)

@router.post("", response_model=Table, status_code=status.HTTP_201_CREATED)
def create_table(table: TableCreate, conn = Depends(get_db), usuario = Depends(verificar_rol("admin"))):
    """Crear una nueva mesa"""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO tables (table_number, is_occupied) VALUES (%s, %s) RETURNING id, table_number, is_occupied",
            (table.table_number, table.is_occupied)
        )
        new_row = cursor.fetchone()
        conn.commit()
        return Table(id=new_row['id'], table_number=new_row['table_number'], is_occupied=new_row['is_occupied'])
    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="El número de mesa ya existe")

@router.patch("/{table_id}/status")
def update_table_status(table_id: int, is_occupied: bool, conn = Depends(get_db), usuario = Depends(obtener_usuario_actual)):
    """Actualizar el estado de una mesa"""
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tables SET is_occupied = %s WHERE id = %s RETURNING id, table_number, is_occupied",
        (is_occupied, table_id)
    )
    updated_table = cursor.fetchone()
    
    if not updated_table:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    
    conn.commit()
    return Table(id=updated_table['id'], table_number=updated_table['table_number'], is_occupied=updated_table['is_occupied'])

@router.patch("/{table_id}/position")
def update_table_position(table_id: int, x: int, y: int, conn = Depends(get_db), usuario = Depends(verificar_rol("admin"))):
    """Actualizar la posición de una mesa (solo admin)"""
    # Validate coordinate range
    if not (0 <= x <= 2000) or not (0 <= y <= 2000):
        raise HTTPException(status_code=400, detail="Coordenadas x/y deben estar entre 0 y 2000")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tables SET x = %s, y = %s WHERE id = %s RETURNING *",
        (x, y, table_id)
    )
    updated_table = cursor.fetchone()
    
    if not updated_table:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    
    conn.commit()
    return Table(
        id=updated_table['id'], 
        table_number=updated_table['table_number'], 
        is_occupied=updated_table['is_occupied'],
        x=updated_table['x'],
        y=updated_table['y']
    )