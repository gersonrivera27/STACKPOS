"""
Router para gestión de clientes
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
import psycopg2

from ..database import get_db
from ..models.customer import Customer, CustomerCreate, CustomerUpdate
from ..security import obtener_usuario_actual, verificar_rol

router = APIRouter()

MAX_SEARCH_LENGTH = 100  # Evita consultas LIKE con strings muy largos
MAX_LIMIT = 200          # Tope absoluto de resultados por request

@router.get("", response_model=List[Customer])
def get_customers(
    search: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=MAX_LIMIT),
    conn = Depends(get_db),
    usuario = Depends(obtener_usuario_actual)
):
    """Obtener todos los clientes con búsqueda opcional"""
    cursor = conn.cursor()

    # Truncar el término de búsqueda para evitar consultas LIKE extremadamente largas
    if search:
        search = search[:MAX_SEARCH_LENGTH]

    if search:
        query = """
            SELECT * FROM customers
            WHERE phone LIKE %s OR name ILIKE %s OR eircode ILIKE %s
            ORDER BY created_at DESC LIMIT %s
        """
        search_pattern = f"%{search}%"
        cursor.execute(query, (search_pattern, search_pattern, search_pattern, limit))
    else:
        query = "SELECT * FROM customers ORDER BY created_at DESC LIMIT %s"
        cursor.execute(query, (limit,))
    
    customers = cursor.fetchall()
    return customers

@router.get("/search-by-phone/{phone}")
def search_by_phone(phone: str, conn = Depends(get_db), usuario = Depends(obtener_usuario_actual)):
    """Buscar cliente por teléfono"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE phone = %s", (phone,))
    customer = cursor.fetchone()
    
    if customer:
        return {"found": True, "customer": dict(customer)}
    return {"found": False, "customer": None}

@router.get("/{customer_id}", response_model=Customer)
def get_customer(customer_id: int, conn = Depends(get_db), usuario = Depends(obtener_usuario_actual)):
    """Obtener un cliente por ID"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
    customer = cursor.fetchone()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return customer

@router.post("", response_model=Customer, status_code=status.HTTP_201_CREATED)
def create_customer(customer: CustomerCreate, conn = Depends(get_db), usuario = Depends(obtener_usuario_actual)):
    """Crear un nuevo cliente"""
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """INSERT INTO customers 
               (phone, name, email, address_line1, address_line2, city, county, 
                eircode, country, latitude, longitude, notes)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
               RETURNING *""",
            (customer.phone, customer.name, customer.email, customer.address_line1,
             customer.address_line2, customer.city, customer.county, customer.eircode,
             customer.country, customer.latitude, customer.longitude, customer.notes)
        )
        new_customer = cursor.fetchone()
        conn.commit()
        return new_customer
    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="El teléfono ya está registrado")

@router.put("/{customer_id}", response_model=Customer)
def update_customer(
    customer_id: int, 
    customer: CustomerUpdate, 
    conn = Depends(get_db),
    usuario = Depends(obtener_usuario_actual)
):
    """Actualizar un cliente"""
    cursor = conn.cursor()
    
    # Construir query dinámicamente
    updates = []
    values = []
    
    if customer.phone is not None:
        updates.append("phone = %s")
        values.append(customer.phone)
    if customer.name is not None:
        updates.append("name = %s")
        values.append(customer.name)
    if customer.email is not None:
        updates.append("email = %s")
        values.append(customer.email)
    if customer.address_line1 is not None:
        updates.append("address_line1 = %s")
        values.append(customer.address_line1)
    if customer.address_line2 is not None:
        updates.append("address_line2 = %s")
        values.append(customer.address_line2)
    if customer.city is not None:
        updates.append("city = %s")
        values.append(customer.city)
    if customer.county is not None:
        updates.append("county = %s")
        values.append(customer.county)
    if customer.eircode is not None:
        updates.append("eircode = %s")
        values.append(customer.eircode)
    if customer.latitude is not None:
        updates.append("latitude = %s")
        values.append(customer.latitude)
    if customer.longitude is not None:
        updates.append("longitude = %s")
        values.append(customer.longitude)
    if customer.notes is not None:
        updates.append("notes = %s")
        values.append(customer.notes)
    if customer.is_active is not None:
        updates.append("is_active = %s")
        values.append(customer.is_active)
    
    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(customer_id)
    
    query = f"UPDATE customers SET {', '.join(updates)} WHERE id = %s RETURNING *"
    cursor.execute(query, values)
    updated_customer = cursor.fetchone()
    
    if not updated_customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    conn.commit()
    return updated_customer

@router.delete("/{customer_id}")
def delete_customer(customer_id: int, conn = Depends(get_db), usuario = Depends(verificar_rol("admin"))):
    """Desactivar un cliente (soft delete). Requiere rol admin."""
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE customers SET is_active = false WHERE id = %s RETURNING id",
        (customer_id,)
    )
    deleted = cursor.fetchone()
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    conn.commit()
    return {"message": "Cliente desactivado correctamente", "id": customer_id}
