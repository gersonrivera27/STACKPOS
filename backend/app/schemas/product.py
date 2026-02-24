from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime


class ProductBase(BaseModel):
    name: str
    category_id: int
    price: Decimal
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_available: bool = True
    sort_order: int = 0
    stock_quantity: int = 0

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    price: Optional[Decimal] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None
    sort_order: Optional[int] = None
    stock_quantity: Optional[int] = None

class Product(ProductBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductWithCategory(Product):
    category_name: str