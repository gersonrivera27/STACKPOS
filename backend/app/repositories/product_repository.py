"""
Repositorio para manejo de productos en base de datos
"""
from typing import List, Optional, Tuple
from decimal import Decimal
import psycopg2
from ..schemas.product import ProductCreate, ProductUpdate

class ProductRepository:
    def __init__(self, conn):
        self.conn = conn

    def category_exists(self, category_id: int) -> bool:
        """Verificar si una categoría existe"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM categories WHERE id = %s", (category_id,))
        return cursor.fetchone() is not None

    def get_all(self, category_id: Optional[int] = None, available_only: bool = True) -> List[dict]:
        """Obtener todos los productos, opcionalmente filtrados por categoría y disponibilidad"""
        cursor = self.conn.cursor()
        
        query_parts = [
            """
            SELECT 
                p.id, p.name, p.category_id, p.price, 
                p.description, p.image_url, p.is_available, 
                p.created_at, p.updated_at,
                c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE 1=1
            """
        ]
        params = []
        
        if available_only:
            query_parts.append("AND p.is_available = TRUE")
            
        if category_id:
            query_parts.append("AND p.category_id = %s")
            params.append(category_id)
            
        query_parts.append("ORDER BY p.name")
        
        cursor.execute(" ".join(query_parts), params)
        return cursor.fetchall()

    def get_by_id(self, product_id: int) -> Optional[dict]:
        """Obtener un producto por su ID"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                p.id, p.name, p.category_id, p.price, 
                p.description, p.image_url, p.is_available, 
                p.created_at, p.updated_at,
                c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s
        """, (product_id,))
        
        return cursor.fetchone()

    def create(self, product: ProductCreate) -> dict:
        """Crear un nuevo producto"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO products (
                name, category_id, price, description, 
                image_url, is_available
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, name, category_id, price, description, 
                      image_url, is_available, created_at, updated_at
        """, (
            product.name, product.category_id, product.price,
            product.description, product.image_url, 
            product.is_available
        ))
        return cursor.fetchone()

    def update(self, product_id: int, product: ProductUpdate) -> Optional[dict]:
        """Actualizar un producto existente"""
        cursor = self.conn.cursor()
        
        updates = []
        values = []
        
        if product.name is not None:
            updates.append("name = %s")
            values.append(product.name)
        
        if product.category_id is not None:
            updates.append("category_id = %s")
            values.append(product.category_id)
        
        if product.price is not None:
            updates.append("price = %s")
            values.append(product.price)
        
        if product.description is not None:
            updates.append("description = %s")
            values.append(product.description)
        
        if product.image_url is not None:
            updates.append("image_url = %s")
            values.append(product.image_url)
        
        if product.is_available is not None:
            updates.append("is_available = %s")
            values.append(product.is_available)
        
        if not updates:
            return None
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(product_id)
        
        query = f"""
            UPDATE products
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING id, name, category_id, price, description, 
                      image_url, is_available, created_at, updated_at
        """
        
        cursor.execute(query, values)
        return cursor.fetchone()

    def delete(self, product_id: int) -> bool:
        """Soft delete de un producto"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE products
            SET is_available = FALSE
            WHERE id = %s
            RETURNING id
        """, (product_id,))
        
        return cursor.fetchone() is not None
