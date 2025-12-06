from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

class OrderType(str, Enum):
    DELIVERY = "delivery"
    TAKEOUT = "takeout"
    COLLECTION = "collection"

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    notes: Optional[str] = None

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    notes: Optional[str] = None

class OrderItem(OrderItemBase):
    id: int
    order_id: int
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    customer_id: int
    order_type: OrderType
    items: List[OrderItemCreate]
    notes: Optional[str] = None
    phone_line: Optional[int] = Field(None, ge=1, le=4)
    delivery_fee: Decimal = Decimal("0.00")
    status: Optional[OrderStatus] = None

class OrderBase(BaseModel):
    customer_id: int
    order_type: OrderType
    status: OrderStatus
    subtotal: Decimal
    tax: Decimal
    delivery_fee: Decimal
    total: Decimal
    notes: Optional[str] = None
    phone_line: Optional[int] = None

class Order(OrderBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class OrderWithItems(Order):
    items: List[OrderItem]