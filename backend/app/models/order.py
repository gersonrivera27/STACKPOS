"""
Modelos Pydantic para Órdenes
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

class OrderType(str, Enum):
    """Tipos de orden"""
    DELIVERY = "delivery"
    TAKEOUT = "takeout"
    DINE_IN = "dine_in"

class OrderStatus(str, Enum):
    """Estados de orden"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentMethod(str, Enum):
    """Métodos de pago"""
    CASH = "cash"
    CARD = "card"
    ONLINE = "online"

class OrderItemCreate(BaseModel):
    """Modelo para crear item de orden"""
    product_id: int
    quantity: int = Field(gt=0, description="Cantidad debe ser mayor a 0")
    special_instructions: Optional[str] = None

class OrderItemBase(BaseModel):
    """Base para item de orden"""
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    special_instructions: Optional[str] = None

class OrderItem(OrderItemBase):
    """Modelo completo de item de orden"""
    id: int
    order_id: int
    created_at: datetime
    product_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    """Modelo para crear orden"""
    customer_name: Optional[str] = None
    order_type: OrderType
    items: List[OrderItemCreate] = Field(min_length=1, description="Debe tener al menos 1 item")
    notes: Optional[str] = None
    table_id: Optional[int] = None
    payment_method: Optional[PaymentMethod] = None

class OrderUpdate(BaseModel):
    """Modelo para actualizar orden"""
    status: Optional[OrderStatus] = None
    customer_name: Optional[str] = None
    notes: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None

class OrderBase(BaseModel):
    """Base para orden"""
    order_number: str
    customer_name: Optional[str] = None
    order_type: str
    status: str
    subtotal: Decimal
    tax: Decimal
    discount: Decimal
    total: Decimal
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    table_id: Optional[int] = None

class Order(OrderBase):
    """Modelo completo de orden"""
    id: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class OrderWithDetails(Order):
    """Orden con items"""
    items: List[OrderItem]