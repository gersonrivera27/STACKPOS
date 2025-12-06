"""
Router para gestión de categorías
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import psycopg2

from ..database import get_db
from ..models.category import Category, CategoryCreate, CategoryUpdate

router = APIRouter()

@router.get("", response_model=List[Category])
def get_categories(conn = Depends(get_db)):
    """Obtener todas las categorías"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, description, created_at
        FROM categories
        ORDER BY name
    """)
    categories = cursor.fetchall()
    return categories

@router.get("/{category_id}", response_model=Category)
def get_category(category_id: int, conn = Depends(get_db)):
    """Obtener categoría por ID"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, description, created_at
        FROM categories
        WHERE id = %s
    """, (category_id,))
    category = cursor.fetchone()
    
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    return category

@router.post("", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate, conn = Depends(get_db)):
    """Crear nueva categoría"""
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO categories (name, description)
            VALUES (%s, %s)
            RETURNING id, name, description, created_at
        """, (category.name, category.description))
        
        new_category = cursor.fetchone()
        conn.commit()
        return new_category
    
    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Ya existe una categoría con ese nombre")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{category_id}", response_model=Category)
def update_category(category_id: int, category: CategoryUpdate, conn = Depends(get_db)):
    """Actualizar categoría"""
    cursor = conn.cursor()
    
    # Construir query dinámicamente
    updates = []
    values = []
    
    if category.name is not None:
        updates.append("name = %s")
        values.append(category.name)
    
    if category.description is not None:
        updates.append("description = %s")
        values.append(category.description)
    
    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    
    values.append(category_id)
    
    query = f"""
        UPDATE categories
        SET {', '.join(updates)}
        WHERE id = %s
        RETURNING id, name, description, created_at
    """
    
    try:
        cursor.execute(query, values)
        updated_category = cursor.fetchone()
        
        if not updated_category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
        conn.commit()
        return updated_category
    
    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Ya existe una categoría con ese nombre")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{category_id}")
def delete_category(category_id: int, conn = Depends(get_db)):
    """Eliminar categoría"""
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM categories
        WHERE id = %s
        RETURNING id
    """, (category_id,))
    
    deleted = cursor.fetchone()
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    conn.commit()
    return {"message": "Categoría eliminada correctamente", "id": category_id}