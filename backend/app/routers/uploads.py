from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from ..security import obtener_usuario_actual
import os
from uuid import uuid4
import filetype
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post("/images", response_model=dict)
async def upload_image(
    file: UploadFile = File(...),
    usuario = Depends(obtener_usuario_actual)
):
    """
    Subir una imagen. Retorna la URL relativa.
    - Requiere autenticación
    - Máximo 5 MB
    - Solo .jpg / .png / .webp (validado por contenido, no solo extensión)
    """
    # Validar extensión del nombre
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Formato no permitido. Use .jpg, .png o .webp"
        )

    # Leer contenido completo con límite de tamaño
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="El archivo excede el límite de 5 MB"
        )

    # Validar tipo real del archivo por su contenido (no solo por extensión)
    kind = filetype.guess(contents)
    if kind is None or kind.mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="El contenido del archivo no corresponde a una imagen válida"
        )

    # Guardar con nombre UUID para evitar colisiones y enumeración
    filename = f"{uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
    except Exception as e:
        logger.error("Error guardando imagen: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error al guardar la imagen")

    return {"url": f"/uploads/{filename}"}
