"""
Config router - Public configuration endpoint
"""
from fastapi import APIRouter
from app.config import settings

router = APIRouter()

@router.get("/api/config/public")
async def get_public_config():
    """
    Get public configuration values (non-sensitive)
    Returns Google Maps API key for client-side use
    """
    return {
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY
    }
