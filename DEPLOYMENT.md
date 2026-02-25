# 🚀 Despliegue — BurgerPOS en Raspberry Pi 5

## Arquitectura

```
Internet → Cloudflare (SSL) → Tunnel → Pi 5 (Docker)
                                         ├── nginx (:8088 → Tunnel)
                                         ├── frontend (Blazor :5000)
                                         ├── backend (FastAPI :8000)
                                         ├── postgres (:5432)
                                         ├── rabbitmq (:5672)
                                         ├── audit-consumer (worker)
                                         └── backup (pg_dump diario)
```

**Dominio:** `pos.gerson-sec.com` via Cloudflare Tunnel  
**No se abren puertos** — el Tunnel conecta de forma saliente.

---

## Paso 1: Clonar en la Pi

```bash
ssh pi@192.168.1.24

# Clonar repositorio
git clone https://github.com/gersonrivera27/Restaurant_pos.git ~/burger-pos
cd ~/burger-pos
```

---

## Paso 2: Configurar Variables de Entorno

### Crear `backend/.env`:
```bash
cp backend/.env.example backend/.env
nano backend/.env
```

Configurar:
```env
ENV=production
DATABASE_URL=postgresql://postgres:TU_PASSWORD@db:5432/burger_pos
SECRET_KEY=<genera con: openssl rand -hex 32>
JWT_SECRET_KEY=<genera con: openssl rand -hex 32>
ALLOWED_ORIGINS=https://pos.gerson-sec.com
RABBITMQ_URL=amqp://burger_mq:TU_MQ_PASS@rabbitmq:5672/
RABBITMQ_ENABLED=true
GOOGLE_MAPS_API_KEY=tu_api_key
```

### Crear `.env.db`:
```bash
cp .env.db.example .env.db
nano .env.db
```

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=TU_PASSWORD
POSTGRES_DB=burger_pos
```

### Crear `.env` raíz para credenciales compartidas:
```bash
cat > .env << 'EOF'
RABBITMQ_USER=burger_mq
RABBITMQ_PASS=TU_MQ_PASS
POSTGRES_PASSWORD=TU_PASSWORD
EOF
```

---

## Paso 3: Levantar BurgerPOS

```bash
cd ~/burger-pos

# Construir y levantar (primera vez tarda ~5-10 min en la Pi)
docker compose -f docker-compose.pi.yml up -d --build

# Verificar que todo está corriendo
docker compose -f docker-compose.pi.yml ps

# Ver logs
docker compose -f docker-compose.pi.yml logs -f
```

Verificar acceso local:
```bash
curl http://localhost:8088/health
# → {"status":"healthy"}
```

---

## Paso 4: Configurar Cloudflare Tunnel

Ya tienes `cloudflared-connector` corriendo. Solo necesitas añadir una ruta nueva.

### Opción A: Desde el Dashboard de Cloudflare (más fácil)

1. Ir a **Cloudflare Dashboard** → **Zero Trust** → **Networks** → **Tunnels**
2. Seleccionar tu tunnel existente → **Configure**
3. Ir a **Public Hostname** → **Add a public hostname**
4. Configurar:

| Campo | Valor |
|-------|-------|
| Subdomain | `pos` |
| Domain | `gerson-sec.com` |
| Type | `HTTP` |
| URL | `192.168.1.24:8088` |

5. En **Additional application settings** → **HTTP Settings**:
   - ✅ **HTTP Host Header**: `pos.gerson-sec.com`
   - ✅ **No TLS Verify**: ON (nginx es HTTP interno)

6. **Save hostname**

### Opción B: Via config YAML (si usas archivo de config)

Añadir al archivo de configuración de cloudflared:
```yaml
ingress:
  # BurgerPOS
  - hostname: pos.gerson-sec.com
    service: http://192.168.1.24:8088
  # ... tus otras rutas existentes
  - service: http_status:404
```

---

## Paso 5: Verificar

1. Esperar ~1 minuto para que Cloudflare propague el DNS
2. Acceder a **https://pos.gerson-sec.com**
3. Login: `admin` / `admin123`
4. **⚠️ Cambiar la contraseña del admin inmediatamente**

---

## Backups

```bash
# Ver backups existentes
docker exec burger-backup ls -lh /backups/

# Backup manual
docker exec burger-backup /backup.sh

# Restaurar un backup
gunzip -c backup.sql.gz | docker exec -i burger-db psql -U postgres -d burger_pos
```

---

## Comandos Útiles

```bash
# Alias recomendado (añadir a ~/.bashrc)
alias burger='docker compose -f ~/burger-pos/docker-compose.pi.yml'

# Entonces puedes usar:
burger ps          # Estado
burger logs -f     # Logs
burger restart     # Reiniciar
burger down        # Parar

# Actualizar desde GitHub
cd ~/burger-pos
git pull
burger up -d --build
```

---

## Monitoreo

Ya tienes **Dozzle** corriendo en la Pi para ver logs de containers.  
BurgerPOS aparecerá automáticamente en Dozzle (burger-frontend, burger-backend, etc.)

**Health check:** `https://pos.gerson-sec.com/health`

---

## Recursos de la Pi

| Servicio | RAM (aprox.) |
|----------|-------------|
| Frontend (Blazor) | ~150 MB |
| Backend (FastAPI) | ~100 MB |
| PostgreSQL | ~50 MB |
| RabbitMQ | ~100 MB |
| Nginx | ~5 MB |
| Audit Consumer | ~50 MB |
| **Total BurgerPOS** | **~450 MB** |
| + Containers existentes | ~300 MB |
| **Total Pi** | **~750 MB / 8 GB** |
