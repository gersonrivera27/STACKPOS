"""
Exportación centralizada de modelos
"""
from .customer import Customer, CustomerCreate, CustomerUpdate
from .category import Category, CategoryCreate, CategoryUpdate
from ..schemas.product import Product, ProductCreate, ProductUpdate, ProductWithCategory
from .order import (
    Order,
    OrderCreate, 
    OrderUpdate,
    OrderItem,
    OrderItemCreate,
    OrderWithDetails,
    OrderStatus,
    OrderType
)
from .table import Table, TableCreate, TableUpdate
from .modifier import Modifier, ModifierCreate, ModifierUpdate

__all__ = [
    # Customers
    "Customer",
    "CustomerCreate", 
    "CustomerUpdate",
    
    # Categories
    "Category",
    "CategoryCreate",
    "CategoryUpdate",
    
    # Products
    "Product",
    "ProductCreate",
    "ProductUpdate",
    "ProductWithCategory",
    
    # Orders
    "Order",
    "OrderCreate",
    "OrderUpdate",
    "OrderItem",
    "OrderItemCreate",
    "OrderWithDetails",
    "OrderStatus",
    "OrderType",
    
    # Tables
    "Table",
    "TableCreate",
    "TableUpdate",
    
    # Modifiers
    "Modifier",
    "ModifierCreate",
    "ModifierUpdate",
]
