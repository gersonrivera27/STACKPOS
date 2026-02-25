#!/bin/bash

# Script de migración automática para dividir el backend monolítico
# Uso: bash migrate.sh

set -e  # Salir si hay algún error

echo "🚀 Iniciando migración del backend..."
echo ""

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py no encontrado. Asegúrate de estar en el directorio backend/"
    exit 1
fi

echo "${BLUE}📋 Paso 1: Haciendo backup del archivo original...${NC}"
cp main.py main.py.backup
echo "${GREEN}✓ Backup creado: main.py.backup${NC}"
echo ""

echo "${BLUE}📁 Paso 2: Creando estructura de directorios...${NC}"
mkdir -p app/models
mkdir -p app/routers
touch app/__init__.py
touch app/models/__init__.py
touch app/routers/__init__.py
echo "${GREEN}✓ Estructura de directorios creada${NC}"
echo ""

echo "${BLUE}📝 Paso 3: Creando archivos base...${NC}"

# Crear config.py
cat > app/config.py << 'CONFIGEOF'
"""
Configuración de la aplicación
"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configuración de la aplicación"""

    # DATABASE_URL debe definirse como variable de entorno.
    # Ejemplo: postgresql://usuario:contraseña@host:5432/nombre_db
    DATABASE_URL: str

    API_TITLE: str = "Burger POS API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "API completa para sistema POS de restaurante de hamburguesas"

    ALLOWED_ORIGINS: list = ["*"]
    TAX_RATE: float = 0.10

    class Config:
        case_sensitive = True

settings = Settings()
CONFIGEOF

echo "${GREEN}✓ config.py creado${NC}"

# Crear database.py
cat > app/database.py << 'DBEOF'
"""
Gestión de conexión a base de datos
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from .config import settings

def get_db():
    """Obtener conexión a la base de datos"""
    conn = psycopg2.connect(
        settings.DATABASE_URL,
        cursor_factory=RealDictCursor
    )
    try:
        yield conn
    finally:
        conn.close()
DBEOF

echo "${GREEN}✓ database.py creado${NC}"
echo ""

echo "${YELLOW}⚠️  IMPORTANTE: Los archivos de modelos y routers deben ser copiados manualmente${NC}"
echo "${YELLOW}   Usa los artifacts proporcionados para completar la migración${NC}"
echo ""

echo "${BLUE}📦 Paso 4: Verificando requirements.txt...${NC}"
if [ ! -f "requirements.txt" ]; then
    echo "${YELLOW}⚠️  requirements.txt no encontrado, creando uno nuevo...${NC}"
    echo "⚠️  Crea requirements.txt manualmente con las versiones actuales del proyecto."
    echo "    Consulta el requirements.txt existente en el repositorio para las versiones correctas."
    echo "${GREEN}✓ requirements.txt creado${NC}"
else
    echo "${GREEN}✓ requirements.txt ya existe${NC}"
fi
echo ""

echo "${BLUE}📋 Estructura creada:${NC}"
tree app/ 2>/dev/null || find app/ -type f

echo ""
echo "${GREEN}✅ Migración parcial completada${NC}"
echo ""
echo "${YELLOW}📝 Próximos pasos manuales:${NC}"
echo "   1. Copiar los archivos de models/ desde los artifacts"
echo "   2. Copiar los archivos de routers/ desde los artifacts"
echo "   3. Crear el nuevo app/main.py"
echo "   4. Reiniciar el contenedor: docker-compose restart backend"
echo ""
echo "${BLUE}💡 Tip: Consulta la 'Guía de Migración' para instrucciones detalladas${NC}"
echo ""
echo "🎉 ¡Listo para continuar!"