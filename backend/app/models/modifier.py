"""
Modelos Pydantic para Modificadores
"""
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class ModifierBase(BaseModel):
    """Base para modificador"""
    name: str
    price: Decimal
    is_active: bool = True

class ModifierCreate(ModifierBase):
    """Modelo para crear modificador"""
    pass

class ModifierUpdate(BaseModel):
    """Modelo para actualizar modificador"""
    name: Optional[str] = None
    price: Optional[Decimal] = None
    is_active: Optional[bool] = None

class Modifier(ModifierBase):
    """Modelo completo de modificador"""
    id: int
    
    class Config:
        from_attributes = True