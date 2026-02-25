FROM python:3.11-slim

WORKDIR /app

# Crear usuario no-root para ejecutar la app
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Instalar dependencias como root (necesario para pip)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código y asignar propiedad al usuario de la app
COPY . .
RUN chown -R appuser:appgroup /app

# Crear directorio de uploads con permisos correctos
RUN mkdir -p /app/uploads && chown appuser:appgroup /app/uploads

# Cambiar a usuario sin privilegios
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
