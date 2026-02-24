"""
Router para gestión de órdenes
"""
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import psycopg2

from ..database import get_db
from ..models.order import (
    Order, OrderCreate, OrderWithDetails, OrderItem,
    OrderItemCreate, OrderStatus, OrderUpdate
)
from pydantic import BaseModel
from .geocoding import calculate_delivery_fee
from app.config import settings

router = APIRouter()

# Import WebSocket manager para notificaciones en tiempo real
try:
    from .websocket_router import notify_order_change, notify_kitchen_update
    WEBSOCKET_AVAILABLE = True
except:
    WEBSOCKET_AVAILABLE = False

def generate_order_number():
    """Generar número de orden único"""
    return f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"

class OrderItemsUpdate(BaseModel):
    """Payload para agregar / quitar items a una orden existente"""
    add_items: list[OrderItemCreate] = []
    remove_item_ids: list[int] = []

@router.post("", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(order_data: OrderCreate, background_tasks: BackgroundTasks, conn = Depends(get_db)):
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
            
            # Calcular modificadores si hay
            modifiers_total = Decimal("0.00")
            item_modifiers_data = []
            
            if hasattr(item, 'modifier_ids') and item.modifier_ids:
                for mod_id in item.modifier_ids:
                    cursor.execute("SELECT id, name, price FROM modifiers WHERE id = %s AND is_active = TRUE", (mod_id,))
                    mod = cursor.fetchone()
                    if mod:
                        modifiers_total += Decimal(str(mod['price']))
                        item_modifiers_data.append(mod)

            # En modelo Tax-Inclusive, el precio del producto es el precio final
            unit_price = Decimal(str(product['price'])) + modifiers_total
            item_total = unit_price * item.quantity
            total += item_total
            
            # Guardamos el item_total como subtotal del item
            order_items_data.append({
                'product_id': product['id'],
                'quantity': item.quantity,
                'unit_price': unit_price,
                'subtotal': item_total,
                'special_instructions': item.special_instructions,
                'modifiers': item_modifiers_data
            })
        
        # Back-calculate Subtotal and Tax from Total (Tax Inclusive)
        # Total = Subtotal * (1 + TAX_RATE)
        tax_multiplier = Decimal(str(1 + settings.TAX_RATE))
        subtotal = total / tax_multiplier
        
        # Tax = Total - Subtotal
        tax = total - subtotal
        
        # Delivery Fee
        delivery_fee = Decimal("0.00")
        if order_data.order_type.value == "delivery":
            if order_data.customer_id:
                cursor.execute("SELECT latitude, longitude FROM customers WHERE id = %s", (order_data.customer_id,))
                cust_coords = cursor.fetchone()
                if cust_coords and cust_coords['latitude'] and cust_coords['longitude']:
                    fee = calculate_delivery_fee(float(cust_coords['latitude']), float(cust_coords['longitude']))
                    delivery_fee = Decimal(str(fee))
                else:
                    delivery_fee = Decimal("3.00")  # Default fee if no coords
            else:
                delivery_fee = Decimal("3.00")  # Default fee if no customer_id provided
                
        # Discount (0 por ahora)
        discount = Decimal("0.00")
        
        # Add delivery fee to total at the end
        total += delivery_fee
        
        # Validar línea telefónica
        if order_data.phone_line is not None:
            cursor.execute("""
                SELECT id FROM orders 
                WHERE phone_line = %s 
                  AND status NOT IN ('completed', 'cancelled')
            """, (order_data.phone_line,))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=400, 
                    detail=f"La línea telefónica {order_data.phone_line} ya está en uso por otra orden activa"
                )

        # 4. Crear orden con cash_session_id
        cursor.execute("""
            INSERT INTO orders (
                order_number, customer_name, order_type, status,
                subtotal, tax, delivery_fee, discount, total,
                payment_method, notes, table_id, cash_session_id, user_id, phone_line
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, order_number, customer_name, order_type, status,
                      subtotal, tax, delivery_fee, discount, total,
                      payment_method, notes, table_id, phone_line,
                      created_at, completed_at, user_id
        """, (
            order_number,
            order_data.customer_name,
            order_data.order_type.value,
            order_data.status.value if order_data.status else OrderStatus.PENDING.value,
            subtotal,
            tax,
            delivery_fee,
            discount,
            total,
            order_data.payment_method.value if order_data.payment_method else None,
            order_data.notes,
            order_data.table_id,
            cash_session_id,
            order_data.user_id,
            order_data.phone_line
        ))
        
        new_order = cursor.fetchone()
        order_id = new_order['id']
        
        # Actualizar estado de mesa si es para comer ahí
        if order_data.table_id:
            cursor.execute("UPDATE tables SET is_occupied = TRUE WHERE id = %s", (order_data.table_id,))
        
        # Crear items de la orden y actualizar inventario
        for item_data in order_items_data:
            cursor.execute("""
                INSERT INTO order_items (
                    order_id, product_id, quantity,
                    unit_price, subtotal, special_instructions
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                order_id,
                item_data['product_id'],
                item_data['quantity'],
                item_data['unit_price'],
                item_data['subtotal'],
                item_data['special_instructions']
            ))
            
            order_item_id = cursor.fetchone()['id']
            
            # Insertar modificadores si existen
            if 'modifiers' in item_data and item_data['modifiers']:
                for mod in item_data['modifiers']:
                    cursor.execute("""
                        INSERT INTO order_item_modifiers (order_item_id, modifier_id, price)
                        VALUES (%s, %s, %s)
                    """, (order_item_id, mod['id'], mod['price']))
            
            # Reducir el inventario del producto
            cursor.execute("""
                UPDATE products 
                SET stock_quantity = GREATEST(0, stock_quantity - %s) 
                WHERE id = %s
            """, (item_data['quantity'], item_data['product_id']))
        
        conn.commit()

        # Notificar via WebSocket en background
        if WEBSOCKET_AVAILABLE:
            background_tasks.add_task(notify_order_change, dict(new_order), 'order_created')

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
            o.subtotal, o.tax, o.delivery_fee, o.discount, o.total,
            o.payment_method, o.notes, o.table_id, o.phone_line,
            o.created_at, o.completed_at, o.user_id,
            u.full_name as waiter_name,
            EXISTS (SELECT 1 FROM payments p WHERE p.order_id = o.id) as has_payment
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
    
    # Obtener modificadores para cada item
    for item in items:
        cursor.execute("""
            SELECT 
                oim.id, oim.modifier_id, oim.price as additional_price,
                m.name as modifier_name
            FROM order_item_modifiers oim
            JOIN modifiers m ON oim.modifier_id = m.id
            WHERE oim.order_item_id = %s
        """, (item['id'],))
        item['modifiers'] = cursor.fetchall()
    
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
            o.subtotal, o.tax, o.delivery_fee, o.discount, o.total,
            o.payment_method, o.notes, o.table_id, o.cash_session_id, o.phone_line,
            o.created_at, o.completed_at, o.user_id,
            u.full_name as waiter_name,
            EXISTS (SELECT 1 FROM payments p WHERE p.order_id = o.id) as has_payment
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

@router.post("/{order_id}/items", response_model=OrderWithDetails)
def update_order_items(
    order_id: int,
    payload: OrderItemsUpdate,
    conn = Depends(get_db)
):
    """Agregar y/o quitar items a una orden existente y recalcular totales."""
    cursor = conn.cursor()
    try:
        # Validar que la orden exista
        cursor.execute("SELECT id FROM orders WHERE id = %s", (order_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Orden no encontrada")

        # Eliminar items solicitados
        if payload.remove_item_ids:
            ids_tuple = tuple(payload.remove_item_ids)
            cursor.execute(
                f"DELETE FROM order_items WHERE order_id = %s AND id IN %s",
                (order_id, ids_tuple)
            )

        # Agregar nuevos items
        for item in payload.add_items:
            cursor.execute("""
                SELECT id, name, price, is_available 
                FROM products 
                WHERE id = %s
            """, (item.product_id,))
            product = cursor.fetchone()
            if not product:
                raise HTTPException(status_code=404, detail=f"Producto {item.product_id} no encontrado")
            if not product['is_available']:
                raise HTTPException(status_code=400, detail=f"Producto {product['name']} no está disponible")

            # Calcular modificadores si hay
            modifiers_total = Decimal("0.00")
            item_modifiers_data = []
            
            if hasattr(item, 'modifier_ids') and item.modifier_ids:
                for mod_id in item.modifier_ids:
                    cursor.execute("SELECT id, name, price FROM modifiers WHERE id = %s AND is_active = TRUE", (mod_id,))
                    mod = cursor.fetchone()
                    if mod:
                        modifiers_total += Decimal(str(mod['price']))
                        item_modifiers_data.append(mod)

            unit_price = Decimal(str(product['price'])) + modifiers_total
            item_total = unit_price * item.quantity

            cursor.execute("""
                INSERT INTO order_items (
                    order_id, product_id, quantity,
                    unit_price, subtotal, special_instructions
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                order_id,
                product['id'],
                item.quantity,
                unit_price,
                item_total,
                item.special_instructions
            ))
            
            order_item_id = cursor.fetchone()['id']
            
            # Insertar modificadores si existen
            for mod in item_modifiers_data:
                cursor.execute("""
                    INSERT INTO order_item_modifiers (order_item_id, modifier_id, price)
                    VALUES (%s, %s, %s)
                """, (order_item_id, mod['id'], mod['price']))

        # Recalcular totales
        cursor.execute("""
            SELECT SUM(subtotal) as total 
            FROM order_items 
            WHERE order_id = %s
        """, (order_id,))
        total_row = cursor.fetchone()
        
        cursor.execute("SELECT delivery_fee FROM orders WHERE id = %s", (order_id,))
        order_row = cursor.fetchone()
        delivery_fee = order_row['delivery_fee'] if order_row else Decimal("0.00")

        items_total = total_row['total'] or Decimal("0.00")
        
        tax_multiplier = Decimal(str(1 + settings.TAX_RATE))
        subtotal = items_total / tax_multiplier if items_total else Decimal("0.00")
        tax = items_total - subtotal
        
        total = items_total + delivery_fee

        cursor.execute("""
            UPDATE orders
            SET subtotal = %s, tax = %s, total = %s
            WHERE id = %s
        """, (subtotal, tax, total, order_id))

        conn.commit()

        # Devolver orden con detalles
        return get_order(order_id, conn)

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{order_id}/status", response_model=Order)
async def update_order_status(
    order_id: int,
    new_status: OrderStatus,
    background_tasks: BackgroundTasks,
    conn = Depends(get_db)
):
    """Actualizar estado de una orden"""
    cursor = conn.cursor()
    
    try:
        # Traer orden actual para validar transiciones/pagos
        cursor.execute("SELECT id, status, payment_method FROM orders WHERE id = %s", (order_id,))
        current = cursor.fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Orden no encontrada")

        # Si el estado es READY o COMPLETED, registrar timestamp
        if new_status in (OrderStatus.READY, OrderStatus.COMPLETED):
            cursor.execute("""
                UPDATE orders
                SET status = %s, completed_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, order_number, customer_name, order_type, status,
                          subtotal, tax, delivery_fee, discount, total,
                          payment_method, notes, table_id, phone_line,
                          created_at, completed_at
            """, (new_status.value, order_id))
        else:
            cursor.execute("""
                UPDATE orders
                SET status = %s
                WHERE id = %s
                RETURNING id, order_number, customer_name, order_type, status,
                          subtotal, tax, delivery_fee, discount, total,
                          payment_method, notes, table_id, phone_line,
                          created_at, completed_at
            """, (new_status.value, order_id))
        
        updated_order = cursor.fetchone()
        
        # Ya validamos existencia arriba, pero mantenemos chequeo defensivo
        if not updated_order:
            raise HTTPException(status_code=404, detail="Orden no encontrada al actualizar")
            
        # Liberar mesa si la orden se completa
        if new_status == OrderStatus.COMPLETED and updated_order['table_id']:
            cursor.execute("UPDATE tables SET is_occupied = FALSE WHERE id = %s", (updated_order['table_id'],))

        conn.commit()

        # Notificar via WebSocket
        if WEBSOCKET_AVAILABLE:
            background_tasks.add_task(notify_order_change, dict(updated_order), 'order_status_changed')

        return updated_order

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
