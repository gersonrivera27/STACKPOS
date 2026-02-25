"""
Aplicación principal FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import asyncio
import logging
from contextlib import asynccontextmanager

from .config import settings
from fastapi.staticfiles import StaticFiles
from .routers import categories, products, orders, modifiers, tables, reports, customers, auth, cash_register, uploads, websocket_router, audit, geocoding
from .middleware.audit_middleware import AuditMiddleware
from .core.rabbitmq import mq

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager
    Se ejecuta al iniciar y cerrar la aplicación
    """
    # Startup: Conectar a RabbitMQ con retry
    if settings.RABBITMQ_ENABLED:
        for attempt in range(1, 6):
            try:
                logger.info("🔄 Conectando a RabbitMQ (intento %d/5)...", attempt)
                await mq.connect()
                logger.info("✅ RabbitMQ conectado exitosamente")
                break
            except Exception as e:
                logger.warning("⚠️ RabbitMQ no disponible: %s", e)
                if attempt < 5:
                    await asyncio.sleep(5)
                else:
                    logger.error("❌ No se pudo conectar a RabbitMQ tras 5 intentos. La app continúa sin él.")

    yield  # La aplicación corre aquí

    # Shutdown: Cerrar conexión a RabbitMQ
    if settings.RABBITMQ_ENABLED:
        logger.info("🔌 Cerrando conexión a RabbitMQ...")
        try:
            await mq.close()
        except Exception as e:
            logger.error(f"Error cerrando RabbitMQ: {str(e)}")


# Crear aplicación - Disable docs in production
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    docs_url=None if settings.ENV == "production" else "/docs",
    redoc_url=None if settings.ENV == "production" else "/redoc",
    openapi_url=None if settings.ENV == "production" else "/openapi.json",
    lifespan=lifespan  # Agregar lifespan
)

# Configurar CORS (debe ser el primer middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Agregar Audit Middleware (después de CORS)
if settings.RABBITMQ_ENABLED:
    app.add_middleware(AuditMiddleware)
    logger.info("✅ Audit Middleware habilitado")
else:
    logger.warning("⚠️ Audit Middleware deshabilitado (RABBITMQ_ENABLED=false)")

# Montar estáticos
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Registrar routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(geocoding.router, tags=["Geocoding"])
app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(modifiers.router, prefix="/api/modifiers", tags=["Modifiers"])
app.include_router(tables.router, prefix="/api/tables", tags=["Tables"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(customers.router, prefix="/api/customers", tags=["Customers"])
app.include_router(cash_register.router, prefix="/api/cash", tags=["Cash Register"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["Uploads"])
app.include_router(websocket_router.router, prefix="/api", tags=["WebSocket"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit Logs"])

# Endpoints principales
@app.get("/")
def read_root():
    """Endpoint raíz"""
    # En producción no exponemos el mapa de rutas
    if settings.ENV == "production":
        return {"status": "ok"}
    return {
        "message": "Burger POS API",
        "status": "running",
        "version": settings.API_VERSION,
        "endpoints": {
            "docs": "/docs",
            "categories": "/api/categories",
            "products": "/api/products",
            "orders": "/api/orders",
            "modifiers": "/api/modifiers",
            "tables": "/api/tables",
            "reports": "/api/reports",
            "customers": "/api/customers",
            "cash": "/api/cash"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)