"""
Configuración de la aplicación
"""
import os
from pydantic import field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Environment
    ENV: str = os.getenv("ENV", "development")
    
    # Base de datos
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # API
    API_TITLE: str = "Burger POS API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "API completa para sistema POS de restaurante de hamburguesas"
    
    # CORS - Configurable via environment
    ALLOWED_ORIGINS: list[str] | str = ["http://localhost:5001", "http://127.0.0.1:5001"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    # Configuración de negocio
    TAX_RATE: float = 0.10  # 10% de impuestos

    # Seguridad - NO DEFAULT VALUES for production
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # JWT Configuration - Must be set via environment
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

    # RabbitMQ Configuration
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "")
    RABBITMQ_ENABLED: bool = os.getenv("RABBITMQ_ENABLED", "true").lower() == "true"

    # Google Maps API
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate required secrets in production
        if self.ENV == "production":
            if not self.SECRET_KEY or not self.JWT_SECRET_KEY:
                raise ValueError("SECRET_KEY and JWT_SECRET_KEY must be set in production!")
            if not self.DATABASE_URL:
                raise ValueError("DATABASE_URL must be set in production!")
    
    class Config:
        case_sensitive = True

settings = Settings()