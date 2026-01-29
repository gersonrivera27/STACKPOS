"""
Modelos Pydantic para Caja/Cash Register
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class CashSessionStatus(str, Enum):
    """Estados de sesión de caja"""
    OPEN = "open"
    CLOSED = "closed"


class PaymentType(str, Enum):
    """Tipos de pago"""
    CASH = "cash"
    CARD = "card"
    MIXED = "mixed"


# ============================================
# SESIÓN DE CAJA
# ============================================
class CashSessionCreate(BaseModel):
    """Crear nueva sesión de caja (apertura)"""
    opening_amount: Decimal = Field(ge=0, description="Monto inicial en caja")
    user_id: int
    notes: Optional[str] = None


class CashSessionClose(BaseModel):
    """Cerrar sesión de caja"""
    closing_amount: Decimal = Field(ge=0, description="Monto final contado")
    notes: Optional[str] = None


class CashSession(BaseModel):
    """Modelo completo de sesión de caja"""
    id: int
    user_id: int
    status: str
    opening_amount: Decimal
    closing_amount: Optional[Decimal] = None
    expected_amount: Optional[Decimal] = None  # Calculado
    difference: Optional[Decimal] = None  # Diferencia entre esperado y contado
    total_cash_sales: Decimal = Decimal("0.00")
    total_card_sales: Decimal = Decimal("0.00")
    total_sales: Decimal = Decimal("0.00")
    total_tips: Decimal = Decimal("0.00")
    orders_count: int = 0
    opened_at: datetime
    closed_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# PAGOS
# ============================================
class PaymentCreate(BaseModel):
    """Crear un pago para una orden"""
    order_id: int
    payment_type: PaymentType
    cash_amount: Decimal = Field(ge=0, default=Decimal("0.00"))
    card_amount: Decimal = Field(ge=0, default=Decimal("0.00"))
    tip_amount: Decimal = Field(ge=0, default=Decimal("0.00"))


class PaymentResponse(BaseModel):
    """Respuesta de pago con cambio calculado"""
    id: int
    order_id: int
    payment_type: str
    total_amount: Decimal
    cash_amount: Decimal
    card_amount: Decimal
    tip_amount: Decimal
    change_amount: Decimal  # Cambio a devolver
    created_at: datetime

    class Config:
        from_attributes = True


class CashSessionSummary(BaseModel):
    """Resumen de caja para cierre"""
    session_id: int
    opening_amount: Decimal
    total_cash_sales: Decimal
    total_card_sales: Decimal
    total_tips: Decimal
    expected_cash: Decimal  # opening + cash_sales + tips
    orders_count: int
    payments: List[PaymentResponse] = []
