from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
from uuid import uuid4
from typing import List

router = APIRouter()

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

@router.post("/images", response_model=dict)
async def upload_image(file: UploadFile = File(...)):
    """
    Subir una imagen. Retorna la URL relativa.
    """
    # Validar extensión
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Formato de archivo no permitido. Use .jpg, .png o .webp")

    # Generar nombre único
    filename = f"{uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # Guardar archivo
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando imagen: {str(e)}")

    # Retornar URL
    return {"url": f"/uploads/{filename}"}
