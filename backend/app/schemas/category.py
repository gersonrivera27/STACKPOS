from pydantic import BaseModel
from typing import Optional

class CategoryBase(BaseModel):
    name: str
    sort_order: int = 0
    is_active: bool = True

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    name: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class Category(CategoryBase):
    id: int
    
    class Config:
        from_attributes = True