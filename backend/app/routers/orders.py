"""
Router para gestión de órdenes
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import psycopg2

from ..database import get_db
from ..models.order import (
    Order, OrderCreate, OrderWithDetails, OrderItem, 
    OrderStatus, OrderUpdate
)

router = APIRouter()

def generate_order_number():
    """Generar número de orden único"""
    return f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"

@router.post("", response_model=Order, status_code=status.HTTP_201_CREATED)
def create_order(order_data: OrderCreate, conn = Depends(get_db)):
    """Crear nueva orden con items"""
    cursor = conn.cursor()
    
    try:
        # Calcular totales
        subtotal = Decimal("0.00")
        order_items_data = []
        
        for item in order_data.items:
            # Obtener producto y verificar disponibilidad
            cursor.execute("""
                SELECT id, name, price, is_available 
                FROM products 
                WHERE id = %s
            """, (item.product_id,))
            
            product = cursor.fetchone()
            
            if not product:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Producto {item.product_id} no encontrado"
                )
            
            if not product['is_available']:
                raise HTTPException(
                    status_code=400,
                    detail=f"Producto {product['name']} no está disponible"
                )
            
            # Calcular subtotal del item
            item_subtotal = Decimal(str(product['price'])) * item.quantity
            subtotal += item_subtotal
            
            order_items_data.append({
                'product_id': product['id'],
                'quantity': item.quantity,
                'unit_price': product['price'],
                'subtotal': item_subtotal,
                'special_instructions': item.special_instructions
            })
        
        # Calcular impuesto (13.5% VAT para Irlanda)
        tax = subtotal * Decimal("0.135")
        
        # Calcular total (subtotal + tax - discount)
        discount = Decimal("0.00")
        total = subtotal + tax - discount
        
        # Generar número de orden
        order_number = generate_order_number()
        
        # Crear orden
        cursor.execute("""
            INSERT INTO orders (
                order_number, customer_name, order_type, status,
                subtotal, tax, discount, total,
                payment_method, notes, table_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, order_number, customer_name, order_type, status,
                      subtotal, tax, discount, total,
                      payment_method, notes, table_id, 
                      created_at, completed_at
        """, (
            order_number,
            order_data.customer_name,
            order_data.order_type.value,
            order_data.status.value if order_data.status else OrderStatus.PENDING.value,
            subtotal,
            tax,
            discount,
            total,
            order_data.payment_method.value if order_data.payment_method else None,
            order_data.notes,
            order_data.table_id
        ))
        
        new_order = cursor.fetchone()
        order_id = new_order['id']
        
        # Crear items de la orden
        for item_data in order_items_data:
            cursor.execute("""
                INSERT INTO order_items (
                    order_id, product_id, quantity,
                    unit_price, subtotal, special_instructions
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                order_id,
                item_data['product_id'],
                item_data['quantity'],
                item_data['unit_price'],
                item_data['subtotal'],
                item_data['special_instructions']
            ))
        
        conn.commit()
        return new_order
    
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{order_id}", response_model=OrderWithDetails)
def get_order(order_id: int, conn = Depends(get_db)):
    """Obtener orden con todos sus detalles"""
    cursor = conn.cursor()
    
    # Obtener orden
    cursor.execute("""
        SELECT 
            id, order_number, customer_name, order_type, status,
            subtotal, tax, discount, total,
            payment_method, notes, table_id,
            created_at, completed_at
        FROM orders
        WHERE id = %s
    """, (order_id,))
    
    order = cursor.fetchone()
    
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    # Obtener items de la orden
    cursor.execute("""
        SELECT 
            oi.id, oi.order_id, oi.product_id, oi.quantity,
            oi.unit_price, oi.subtotal, oi.special_instructions,
            oi.created_at,
            p.name as product_name
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = %s
    """, (order_id,))
    
    items = cursor.fetchall()
    
    # Construir respuesta
    order_dict = dict(order)
    order_dict['items'] = items
    
    return order_dict

@router.get("", response_model=List[Order])
def get_orders(
    status: Optional[str] = None,
    order_type: Optional[str] = None,
    limit: int = 50,
    conn = Depends(get_db)
):
    """Obtener órdenes con filtros opcionales"""
    cursor = conn.cursor()
    
    query = """
        SELECT 
            id, order_number, customer_name, order_type, status,
            subtotal, tax, discount, total,
            payment_method, notes, table_id,
            created_at, completed_at
        FROM orders
        WHERE 1=1
    """
    
    params = []
    
    if status:
        query += " AND status = %s"
        params.append(status)
    
    if order_type:
        query += " AND order_type = %s"
        params.append(order_type)
    
    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)
    
    cursor.execute(query, params)
    orders = cursor.fetchall()
    
    return orders

@router.patch("/{order_id}/status", response_model=Order)
def update_order_status(
    order_id: int,
    new_status: OrderStatus,
    conn = Depends(get_db)
):
    """Actualizar estado de una orden"""
    cursor = conn.cursor()
    
    try:
        # Si el estado es completado, actualizar completed_at
        if new_status == OrderStatus.COMPLETED:
            cursor.execute("""
                UPDATE orders
                SET status = %s, completed_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, order_number, customer_name, order_type, status,
                          subtotal, tax, discount, total,
                          payment_method, notes, table_id,
                          created_at, completed_at
            """, (new_status.value, order_id))
        else:
            cursor.execute("""
                UPDATE orders
                SET status = %s
                WHERE id = %s
                RETURNING id, order_number, customer_name, order_type, status,
                          subtotal, tax, discount, total,
                          payment_method, notes, table_id,
                          created_at, completed_at
            """, (new_status.value, order_id))
        
        updated_order = cursor.fetchone()
        
        if not updated_order:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        
        conn.commit()
        return updated_order
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))