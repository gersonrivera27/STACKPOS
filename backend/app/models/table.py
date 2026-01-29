from pydantic import BaseModel
from typing import Optional, Any
from decimal import Decimal
from datetime import datetime

class TableBase(BaseModel):
    """Base para mesa"""
    table_number: int
    is_occupied: bool = False
    x: int = 0
    y: int = 0

class TableCreate(TableBase):
    """Modelo para crear mesa"""
    pass

class TableUpdate(BaseModel):
    """Modelo para actualizar mesa"""
    table_number: Optional[int] = None
    is_occupied: Optional[bool] = None
    x: Optional[int] = None
    y: Optional[int] = None

class ActiveOrderInfo(BaseModel):
    id: int
    customer_name: Optional[str] = None
    total: Decimal
    created_at: datetime
    time_elapsed: str

class Table(TableBase):
    """Modelo completo de mesa con info de orden activa"""
    id: int
    active_order: Optional[ActiveOrderInfo] = None

    class Config:
        from_attributes = True
