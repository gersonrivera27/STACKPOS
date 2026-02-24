"""
Router para sistema de caja y pagos
"""
from fastapi import APIRouter, HTTPException, Depends, status
from ..security import obtener_usuario_actual
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from ..database import get_db
from ..models.cash_register import (
    CashSessionCreate, CashSessionClose, CashSession, CashSessionSummary,
    PaymentCreate, PaymentResponse, CashSessionStatus
)

router = APIRouter()


# ============================================
# SESIONES DE CAJA
# ============================================

@router.post("/sessions", response_model=CashSession, status_code=status.HTTP_201_CREATED)
def open_cash_session(session_data: CashSessionCreate, conn = Depends(get_db), usuario = Depends(obtener_usuario_actual)):
    """Abrir una nueva sesión de caja"""
    cursor = conn.cursor()
    
    try:
        # Verificar si hay una sesión abierta para este usuario
        cursor.execute("""
            SELECT id FROM cash_sessions 
            WHERE user_id = %s AND status = 'open'
        """, (session_data.user_id,))
        
        existing = cursor.fetchone()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Ya existe una sesión de caja abierta para este usuario"
            )
        
        # Crear nueva sesión
        cursor.execute("""
            INSERT INTO cash_sessions (user_id, opening_amount, notes, status)
            VALUES (%s, %s, %s, 'open')
            RETURNING id, user_id, status, opening_amount, closing_amount,
                      expected_amount, difference, total_cash_sales, total_card_sales,
                      total_sales, total_tips, orders_count, opened_at, closed_at, notes
        """, (session_data.user_id, session_data.opening_amount, session_data.notes))
        
        new_session = cursor.fetchone()
        conn.commit()
        
        return new_session
    
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/active", response_model=Optional[CashSession])
def get_active_session(user_id: Optional[int] = None, conn = Depends(get_db), usuario = Depends(obtener_usuario_actual)):
    """Obtener sesión de caja activa (abierta)"""
    cursor = conn.cursor()
    
    query = """
        SELECT id, user_id, status, opening_amount, closing_amount,
               expected_amount, difference, total_cash_sales, total_card_sales,
               total_sales, total_tips, orders_count, opened_at, closed_at, notes
        FROM cash_sessions
        WHERE status = 'open'
    """
    params = []
    
    if user_id:
        query += " AND user_id = %s"
        params.append(user_id)
    
    query += " ORDER BY opened_at DESC LIMIT 1"
    
    cursor.execute(query, params if params else None)
    session = cursor.fetchone()
    
    return session


@router.get("/sessions/{session_id}", response_model=CashSession)
def get_session(session_id: int, conn = Depends(get_db), usuario = Depends(obtener_usuario_actual)):
    """Obtener detalles de una sesión de caja"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, user_id, status, opening_amount, closing_amount,
               expected_amount, difference, total_cash_sales, total_card_sales,
               total_sales, total_tips, orders_count, opened_at, closed_at, notes
        FROM cash_sessions
        WHERE id = %s
    """, (session_id,))
    
    session = cursor.fetchone()
    
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    return session


@router.get("/sessions/{session_id}/summary", response_model=CashSessionSummary)
def get_session_summary(session_id: int, conn = Depends(get_db), usuario = Depends(obtener_usuario_actual)):
    """Obtener resumen de sesión para cierre"""
    cursor = conn.cursor()
    
    # Obtener sesión
    cursor.execute("""
        SELECT id, opening_amount, total_cash_sales, total_card_sales,
               COALESCE(total_tips, 0) as total_tips, orders_count
        FROM cash_sessions
        WHERE id = %s
    """, (session_id,))
    
    session = cursor.fetchone()
    
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    # Obtener pagos de esta sesión
    cursor.execute("""
        SELECT id, order_id, payment_type, total_amount, cash_amount,
               card_amount, tip_amount, change_amount, created_at
        FROM payments
        WHERE cash_session_id = %s
        ORDER BY created_at DESC
    """, (session_id,))
    
    payments = cursor.fetchall()
    
    # Calcular efectivo esperado
    expected_cash = (
        Decimal(str(session['opening_amount'])) + 
        Decimal(str(session['total_cash_sales'])) +
        Decimal(str(session['total_tips']))
    )
    
    return {
        "session_id": session['id'],
        "opening_amount": session['opening_amount'],
        "total_cash_sales": session['total_cash_sales'],
        "total_card_sales": session['total_card_sales'],
        "total_tips": session['total_tips'],
        "expected_cash": expected_cash,
        "orders_count": session['orders_count'],
        "payments": payments
    }


@router.post("/sessions/{session_id}/close", response_model=CashSession)
def close_cash_session(
    session_id: int, 
    close_data: CashSessionClose, 
    conn = Depends(get_db),
    usuario = Depends(obtener_usuario_actual)
):
    """Cerrar sesión de caja"""
    cursor = conn.cursor()
    
    try:
        # Obtener sesión actual
        cursor.execute("""
            SELECT opening_amount, total_cash_sales, COALESCE(total_tips, 0) as total_tips
            FROM cash_sessions
            WHERE id = %s AND status = 'open'
        """, (session_id,))
        
        session = cursor.fetchone()
        
        if not session:
            raise HTTPException(
                status_code=404, 
                detail="Sesión no encontrada o ya está cerrada"
            )
        
        # Calcular monto esperado y diferencia
        expected = (
            Decimal(str(session['opening_amount'])) + 
            Decimal(str(session['total_cash_sales'])) +
            Decimal(str(session['total_tips']))
        )
        difference = close_data.closing_amount - expected
        
        # Cerrar sesión
        cursor.execute("""
            UPDATE cash_sessions
            SET status = 'closed',
                closing_amount = %s,
                expected_amount = %s,
                difference = %s,
                closed_at = CURRENT_TIMESTAMP,
                notes = COALESCE(notes || ' | ', '') || COALESCE(%s, '')
            WHERE id = %s
            RETURNING id, user_id, status, opening_amount, closing_amount,
                      expected_amount, difference, total_cash_sales, total_card_sales,
                      total_sales, total_tips, orders_count, opened_at, closed_at, notes
        """, (close_data.closing_amount, expected, difference, close_data.notes, session_id))
        
        closed_session = cursor.fetchone()
        conn.commit()
        
        return closed_session
    
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# PAGOS
# ============================================

@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(payment_data: PaymentCreate, conn = Depends(get_db), usuario = Depends(obtener_usuario_actual)):
    """Registrar un pago para una orden"""
    cursor = conn.cursor()
    
    try:
        # Obtener la orden y verificar que existe
        cursor.execute("""
            SELECT id, total, status FROM orders WHERE id = %s
        """, (payment_data.order_id,))
        
        order = cursor.fetchone()
        
        if not order:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        
        if order['status'] == 'completed':
            raise HTTPException(status_code=400, detail="Esta orden ya está pagada")
        
        # Calcular total pagado y cambio
        total_paid = payment_data.cash_amount + payment_data.card_amount
        order_total = Decimal(str(order['total']))
        
        if total_paid < order_total:
            raise HTTPException(
                status_code=400, 
                detail=f"Monto insuficiente. Total: {order_total}, Pagado: {total_paid}"
            )
        
        change_amount = total_paid - order_total
        
        # Obtener sesión de caja activa (opcional)
        cursor.execute("""
            SELECT id FROM cash_sessions WHERE status = 'open' LIMIT 1
        """)
        active_session = cursor.fetchone()
        session_id = active_session['id'] if active_session else None
        
        # Crear registro de pago
        cursor.execute("""
            INSERT INTO payments (
                order_id, cash_session_id, payment_type,
                total_amount, cash_amount, card_amount, tip_amount, change_amount
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, order_id, payment_type, total_amount, cash_amount,
                      card_amount, tip_amount, change_amount, created_at
        """, (
            payment_data.order_id,
            session_id,
            payment_data.payment_type.value,
            order_total,
            payment_data.cash_amount,
            payment_data.card_amount,
            payment_data.tip_amount,
            change_amount
        ))
        
        new_payment = cursor.fetchone()
        
        # Marcar método de pago pero NO cambiar el estado de preparación/cocina.
        # Esto mantiene la orden visible en cocina aunque ya esté pagada.
        cursor.execute("""
            UPDATE orders 
            SET payment_method = %s
            WHERE id = %s
        """, (payment_data.payment_type.value, payment_data.order_id))
        
        conn.commit()
        
        return new_payment
    
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payments/order/{order_id}", response_model=Optional[PaymentResponse])
def get_payment_by_order(order_id: int, conn = Depends(get_db), usuario = Depends(obtener_usuario_actual)):
    """Obtener pago de una orden específica"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, order_id, payment_type, total_amount, cash_amount,
               card_amount, tip_amount, change_amount, created_at
        FROM payments
        WHERE order_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (order_id,))
    
    payment = cursor.fetchone()
    return payment


@router.get("/sessions", response_model=List[CashSession])
def get_sessions(
    status: Optional[str] = None,
    limit: int = 20,
    conn = Depends(get_db),
    usuario = Depends(obtener_usuario_actual)
):
    """Listar sesiones de caja"""
    cursor = conn.cursor()
    
    query = """
        SELECT id, user_id, status, opening_amount, closing_amount,
               expected_amount, difference, total_cash_sales, total_card_sales,
               total_sales, total_tips, orders_count, opened_at, closed_at, notes
        FROM cash_sessions
        WHERE 1=1
    """
    params = []
    
    if status:
        query += " AND status = %s"
        params.append(status)
    
    query += " ORDER BY opened_at DESC LIMIT %s"
    params.append(limit)
    
    cursor.execute(query, params)
    sessions = cursor.fetchall()
    
    return sessions
