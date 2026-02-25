"""
Router para gestión de productos
"""
from fastapi import APIRouter, HTTPException, Depends, status
from ..security import obtener_usuario_actual, verificar_rol
from typing import List, Optional

from ..database import get_db
import logging
logger = logging.getLogger(__name__)
from ..schemas.product import Product, ProductCreate, ProductUpdate, ProductWithCategory
from ..repositories.product_repository import ProductRepository

router = APIRouter()

@router.get("", response_model=List[ProductWithCategory])
def get_products(
    category_id: Optional[int] = None,
    available_only: bool = True,
    conn = Depends(get_db),
    usuario = Depends(obtener_usuario_actual)
):
    """Obtener todos los productos disponibles"""
    repo = ProductRepository(conn)
    return repo.get_all(category_id, available_only)

@router.get("/{product_id}", response_model=ProductWithCategory)
def get_product(product_id: int, conn = Depends(get_db), usuario = Depends(obtener_usuario_actual)):
    """Obtener producto por ID"""
    repo = ProductRepository(conn)
    product = repo.get_by_id(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    return product

@router.post("", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, conn = Depends(get_db), usuario = Depends(verificar_rol("admin"))):
    """Crear nuevo producto"""
    repo = ProductRepository(conn)
    
    # Verificar que la categoría existe
    if not repo.category_exists(product.category_id):
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    try:
        new_product = repo.create(product)
        conn.commit()
        return new_product
    
    except Exception as e:
        conn.rollback()
        logger.error("Error interno: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="Error procesando la solicitud")

@router.put("/{product_id}", response_model=Product)
def update_product(product_id: int, product: ProductUpdate, conn = Depends(get_db), usuario = Depends(verificar_rol("admin"))):
    """Actualizar producto"""
    repo = ProductRepository(conn)
    
    if product.category_id is not None:
        if not repo.category_exists(product.category_id):
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    try:
        updated_product = repo.update(product_id, product)
        
        if not updated_product:
            # Si devuelve None, puede ser que no existe el producto o no hubo campos para actualizar
            # Verificamos si existe el producto primero para dar el error correcto
            if not repo.get_by_id(product_id):
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            # Si existe pero no hubo updates (lista vacía en repo), lanzamos 400
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        conn.commit()
        return updated_product
    
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error("Error interno: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="Error procesando la solicitud")

@router.delete("/{product_id}")
def delete_product(product_id: int, conn = Depends(get_db), usuario = Depends(verificar_rol("admin"))):
    """Desactivar producto (soft delete)"""
    repo = ProductRepository(conn)
    
    if not repo.delete(product_id):
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    conn.commit()
    return {"message": "Producto desactivado correctamente", "id": product_id}