from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TableBase(BaseModel):
    """Base para mesa"""
    table_number: int
    capacity: int
    status: str = "available"  # 'available', 'occupied', 'reserved'

class TableCreate(TableBase):
    """Modelo para crear mesa"""
    pass

class TableUpdate(BaseModel):
    """Modelo para actualizar mesa"""
    table_number: Optional[int] = None
    capacity: Optional[int] = None
    status: Optional[str] = None

class Table(TableBase):
    """Modelo completo de mesa"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
