# 🚀 Guía de Despliegue - BurgerPOS

## Arquitectura de Producción

```
Internet → Cloudflare → Servidor Madrid (Docker)
                              ├── nginx (puerto 80/443)
                              ├── frontend (Blazor)
                              ├── backend (FastAPI)
                              └── postgres (base de datos)
```

---

## Paso 1: Preparar el Servidor

### En el servidor de Madrid, ejecutar:

```bash
# Clonar el repositorio
git clone https://github.com/gersonrivera27/Restaurant_pos.git
cd Restaurant_pos

# Crear archivos de entorno
cp backend/.env.example backend/.env
cp .env.db.example .env.db
cp docker-compose.prod.example.yml docker-compose.prod.yml
```

### Editar `backend/.env`:

```bash
nano backend/.env
```

Cambiar a:
```env
ENV=production
DATABASE_URL=postgresql://postgres:TU_PASSWORD_SEGURO@db:5432/burger_pos
ALLOWED_ORIGINS=https://tudominio.com
SECRET_KEY=genera_con_openssl_rand_hex_32
JWT_SECRET_KEY=genera_otro_con_openssl_rand_hex_32
```

### Editar `.env.db`:

```bash
nano .env.db
```

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=TU_PASSWORD_SEGURO
POSTGRES_DB=burger_pos
```

---

## Paso 2: Configurar Cloudflare

### En el panel de Cloudflare:

1. **DNS**: Añadir registro A
   - Name: `@` o `burgerpos`
   - Content: IP pública del servidor en Madrid
   - Proxy: ✅ Proxied (naranja)

2. **SSL/TLS**: Modo "Full" o "Full (strict)"

3. **Page Rules** (opcional):
   - Always Use HTTPS

---

## Paso 3: Configurar nginx para Cloudflare

Ya creamos `nginx/nginx.conf` con la configuración necesaria.

Para SSL con Cloudflare, el servidor solo necesita HTTP (puerto 80) porque Cloudflare maneja el SSL.

---

## Paso 4: Iniciar en Producción

```bash
# Construir y levantar
docker-compose -f docker-compose.prod.yml up -d

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f

# Verificar estado
docker-compose -f docker-compose.prod.yml ps
```

---

## Paso 5: Verificar

1. Acceder a `https://tudominio.com`
2. Login con el usuario `admin` y la contraseña que generaste en el paso de creación del admin
3. Cambiar la contraseña del admin desde el panel de administración

---

## Comandos Útiles

```bash
# Reiniciar servicios
docker-compose -f docker-compose.prod.yml restart

# Ver logs de un servicio
docker-compose -f docker-compose.prod.yml logs backend

# Actualizar desde GitHub
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## Actualizar Google Maps API Key

En Google Cloud Console, añadir tu dominio de producción:
```
https://tudominio.com/*
```
