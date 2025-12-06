"""
Aplicación principal FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from .config import settings
from .routers import categories, products, orders, modifiers, tables, reports, customers, auth

# Crear aplicación - Disable docs in production
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    docs_url=None if settings.ENV == "production" else "/docs",
    redoc_url=None if settings.ENV == "production" else "/redoc",
    openapi_url=None if settings.ENV == "production" else "/openapi.json"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(modifiers.router, prefix="/api/modifiers", tags=["Modifiers"])
app.include_router(tables.router, prefix="/api/tables", tags=["Tables"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(customers.router, prefix="/api/customers", tags=["Customers"])

# Endpoints principales
@app.get("/")
def read_root():
    """Endpoint raíz con información de la API"""
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
            "customers": "/api/customers"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)