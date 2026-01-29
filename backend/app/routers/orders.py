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
    """Crear nueva orden con items vinculada a la sesión de caja activa"""
    cursor = conn.cursor()
    
    try:
        # 1. Obtener sesión de caja activa
        cursor.execute("""
            SELECT id FROM cash_sessions 
            WHERE status = 'open' 
            ORDER BY id DESC LIMIT 1
        """)
        active_session = cursor.fetchone()
        cash_session_id = active_session['id'] if active_session else None
        
        # 2. Generar número de orden
        if cash_session_id:
            # Si hay sesión, contar órdenes de esta sesión
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM orders 
                WHERE cash_session_id = %s
            """, (cash_session_id,))
            result = cursor.fetchone()
            count = result['count'] if result else 0
            # Formato: #001
            order_number = f"#{count + 1:03d}"
        else:
            # Fallback si no hay sesión (usar timestamp)
            order_number = f"ORD-{datetime.now().strftime('%H%M%S')}"

        # 3. Calcular totales
        total = Decimal("0.00")
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
            
            # En modelo Tax-Inclusive, el precio del producto es el precio final
            item_total = Decimal(str(product['price'])) * item.quantity
            total += item_total
            
            # Guardamos el item_total como subtotal del item
            order_items_data.append({
                'product_id': product['id'],
                'quantity': item.quantity,
                'unit_price': product['price'],
                'subtotal': item_total,
                'special_instructions': item.special_instructions
            })
        
        # Back-calculate Subtotal and Tax from Total (Tax Inclusive)
        # Total = Subtotal * 1.135 -> Subtotal = Total / 1.135
        subtotal = total / Decimal("1.135")
        
        # Tax = Total - Subtotal
        tax = total - subtotal
        
        # Discount (0 por ahora)
        discount = Decimal("0.00")
        
        # 4. Crear orden con cash_session_id
        cursor.execute("""
            INSERT INTO orders (
                order_number, customer_name, order_type, status,
                subtotal, tax, discount, total,
                payment_method, notes, table_id, cash_session_id, user_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, order_number, customer_name, order_type, status,
                      subtotal, tax, discount, total,
                      payment_method, notes, table_id, 
                      created_at, completed_at, user_id
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
            order_data.table_id,
            cash_session_id,
            order_data.user_id
        ))
        
        new_order = cursor.fetchone()
        order_id = new_order['id']
        
        # Actualizar estado de mesa si es para comer ahí
        if order_data.table_id:
            cursor.execute("UPDATE tables SET is_occupied = TRUE WHERE id = %s", (order_data.table_id,))
        
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
        import traceback
        traceback.print_exc()
        print(f"Error creating order: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{order_id}", response_model=OrderWithDetails)
def get_order(order_id: int, conn = Depends(get_db)):
    """Obtener orden con todos sus detalles"""
    cursor = conn.cursor()
    
    # Obtener orden
    # Obtener orden con mesero
    cursor.execute("""
        SELECT 
            o.id, o.order_number, o.customer_name, o.order_type, o.status,
            o.subtotal, o.tax, o.discount, o.total,
            o.payment_method, o.notes, o.table_id,
            o.created_at, o.completed_at, o.user_id,
            u.full_name as waiter_name
        FROM orders o
        LEFT JOIN users u ON o.user_id = u.id
        WHERE o.id = %s
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
    only_active_session: bool = False,
    limit: int = 50,
    conn = Depends(get_db)
):
    """Obtener órdenes con filtros opcionales"""
    cursor = conn.cursor()
    
    query = """
        SELECT 
            o.id, o.order_number, o.customer_name, o.order_type, o.status,
            o.subtotal, o.tax, o.discount, o.total,
            o.payment_method, o.notes, o.table_id, o.cash_session_id,
            o.created_at, o.completed_at, o.user_id,
            u.full_name as waiter_name
        FROM orders o
        LEFT JOIN users u ON o.user_id = u.id
        WHERE 1=1
    """
    
    params = []
    
    # Filtro por sesión activa
    if only_active_session:
        # Buscar la sesión abierta más reciente
        cursor.execute("SELECT id FROM cash_sessions WHERE status = 'open' ORDER BY id DESC LIMIT 1")
        active_session = cursor.fetchone()
        
        if active_session:
            query += " AND cash_session_id = %s"
            params.append(active_session['id'])
        else:
            # Si no hay sesión activa y se pide filtro, no devolver nada (o manejar según lógica de negocio)
            # Retornar lista vacía ya que no hay 'órdenes de la sesión activa'
            return []
    
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
            
        # Liberar mesa si la orden se completa
        if new_status == OrderStatus.COMPLETED and updated_order['table_id']:
            cursor.execute("UPDATE tables SET is_occupied = FALSE WHERE id = %s", (updated_order['table_id'],))
            
        conn.commit()
        return updated_order
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))