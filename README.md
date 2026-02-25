# StackPOS - Restaurant Point of Sale System

[![CI](https://github.com/gersonrivera27/STACKPOS/actions/workflows/ci.yml/badge.svg)](https://github.com/gersonrivera27/STACKPOS/actions/workflows/ci.yml)

**Version:** 3.0 | **Status:** Production Ready

A modern, full-stack Point of Sale (POS) system designed for restaurants handling dine-in, takeaway, and delivery orders. Built with .NET 8.0 Blazor Server and Python FastAPI, featuring real-time kitchen displays, cash register management, Google Maps integration for Eircode address lookup, and comprehensive reporting.

---

## Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **Frontend** | .NET Blazor Server | 8.0 |
| **Backend** | Python FastAPI | 0.104.1 |
| **Database** | PostgreSQL | 15 |
| **Message Queue** | RabbitMQ | 3.12 |
| **ASGI Server** | Uvicorn | 0.24.0 |
| **Containerization** | Docker Compose | Latest |
| **Authentication** | JWT + Bcrypt | python-jose 3.3.0 |
| **Maps Integration** | Google Maps API (Places, Geocoding) | Weekly |
| **State Management** | Blazored.LocalStorage | 4.5.0 |

---

## Implemented Features

### Authentication & Security
- JWT-based authentication with 24-hour token expiration
- PIN login for quick staff access (4-digit codes)
- Role-based access control (admin/staff)
- Bcrypt password hashing (12 rounds)
- Audit logging via RabbitMQ (login attempts, security events)

### Customer Management
- Full CRUD operations with soft delete
- Phone-based lookup and search
- **Eircode address lookup** with multi-strategy resolution:
  - Google Geocoding API (exact street-level addresses)
  - Google Places Text Search (frontend fallback)
  - Nominatim reverse geocoding (free fallback)
  - Eircode prefix map (100+ Irish area codes)
- Google Maps Places Autocomplete for manual address entry
- Automatic latitude/longitude capture for deliveries
- Customer statistics (total orders, total spent)

### Product Catalog
- Category-based organization (Burgers, Sides, Drinks, Desserts)
- Product CRUD with image support
- Price management with tax-inclusive pricing (13.5% VAT)
- Availability toggle
- Product modifiers (Extra Cheese, No Onions, etc.)
- Admin interface for catalog management

### Order Management
- Multi-step order creation with shopping cart
- Three order types: Delivery, Takeaway, Dine-in
- Special instructions per item
- Order status lifecycle: Pending → Confirmed → Preparing → Ready → Completed
- Search and filter by order ID, phone, or status
- Phone line system (track 4 concurrent orders)
- Sequential order numbers (#001, #002, etc.)
- Automatic cash session linking

### Kitchen Display System
- Real-time order queue with auto-refresh (5-second intervals)
- Two-column layout: Pending vs Preparing orders
- Visual order cards with item breakdown
- Status transition buttons
- Order age tracking

### Cash Register & Payment System
- Cash session management (open/close shifts)
- Split payments (cash + card combinations)
- Change calculation and tip handling
- Session summaries with expected vs actual amounts
- Payment history tracking
- Automatic order linking to active sessions

### Printing System
- Print preview with visual ticket display
- Multi-station routing (Kitchen, Bar, Customer)
- Receipt and kitchen ticket templates
- Thermal printer optimization (80mm width)
- Browser-based printing via window.print()

### Reports & Analytics
- Daily sales summary (total sales, orders, average ticket, tax)
- Sales breakdown by order type
- Top-selling products with quantities and revenue
- Revenue by period (day/week/month)
- Completion rate tracking

### Table Management
- Table status management (available, occupied, reserved)
- Table assignment to dine-in orders
- Visual grid with color-coded status
- Auto-release on order completion
- 10 pre-configured tables

### Audit & Monitoring
- RabbitMQ-based event logging
- Login/logout tracking with IP addresses
- Security event monitoring
- WebSocket support for real-time updates

---

## Project Structure

```
burguer/
├── frontend/                              # .NET 8.0 Blazor Server
│   └── BurgerPOS/
│       ├── Components/
│       │   ├── Pages/                     # Application pages
│       │   ├── Shared/                    # Reusable components
│       │   └── Layout/                    # Application layout
│       ├── Services/                      # API clients and auth
│       ├── Models/                        # Domain models
│       ├── wwwroot/
│       │   ├── css/                       # Modular stylesheets
│       │   └── js/
│       │       ├── google-maps.js         # Places Autocomplete
│       │       └── eircode-maps-v2.js     # Eircode lookup logic
│       ├── Program.cs
│       └── Dockerfile.dev                 # Development image
│
├── backend/                               # Python 3.11 FastAPI
│   ├── app/
│   │   ├── main.py                        # Application entry
│   │   ├── config.py                      # Configuration
│   │   ├── database.py                    # PostgreSQL connection
│   │   ├── security.py                    # JWT & auth
│   │   ├── routers/                       # API routers (12+)
│   │   │   ├── geocoding.py              # Eircode multi-strategy lookup
│   │   │   ├── audit.py                  # Audit logging
│   │   │   ├── websocket_router.py       # WebSocket support
│   │   │   └── ...                       # Orders, products, etc.
│   │   ├── models/                        # SQLAlchemy models
│   │   ├── schemas/                       # Pydantic schemas
│   │   ├── repositories/                  # Data access layer
│   │   ├── services/                      # Business logic
│   │   ├── core/                          # RabbitMQ, middleware
│   │   └── consumers/                     # Message consumers
│   ├── init.sql                           # Database schema
│   ├── requirements.txt                   # Python dependencies
│   └── Dockerfile.dev                     # Development image
│
├── nginx/
│   └── nginx.conf                         # Reverse proxy config
│
├── docs/                                  # Documentation
│   ├── API.md                             # API reference
│   └── USER_MANUAL.md                     # Staff training guide
│
├── docker-compose.yml                     # Development environment
├── docker-compose.prod.example.yml        # Production template
├── DEPLOYMENT.md                          # Deployment guide
└── .env.db.example                        # Database credentials template
```

---

## Database Schema

### Core Tables

| Table | Description | Key Features |
|-------|-------------|--------------|
| **users** | Staff accounts | JWT auth, PIN login, roles |
| **customers** | Customer database | Phone-based, geocoding, auto stats |
| **categories** | Product categories | 4 pre-seeded categories |
| **products** | Product catalog | 19 pre-seeded products |
| **orders** | Customer orders | Status lifecycle, sequential numbers |
| **order_items** | Order line items | Quantities, special instructions |
| **tables** | Restaurant tables | 10 pre-configured tables |
| **modifiers** | Product add-ons | 5 pre-seeded modifiers |
| **cash_sessions** | Cash drawer shifts | Expected vs actual tracking |
| **payments** | Payment records | Cash/card/mixed, tips, change |

---

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git
- Google Maps API key (for Eircode lookup & address autocomplete)

### Installation

```bash
# Clone repository
git clone https://github.com/gersonrivera27/STACKPOS.git
cd burguer

# Create environment files
cp backend/.env.example backend/.env
cp .env.db.example .env.db

# Edit backend/.env
nano backend/.env
# Set: ENV, SECRET_KEY, JWT_SECRET_KEY, GOOGLE_MAPS_API_KEY, DATABASE_URL, ALLOWED_ORIGINS

# Edit .env.db
nano .env.db
# Set: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB

# Start all services
docker compose up -d

# View logs
docker compose logs -f
```

### Access Application

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:5001 | Main POS interface |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Swagger UI (dev only) |
| **RabbitMQ** | http://localhost:15672 | Message queue management |
| **Database** | localhost:5433 | PostgreSQL |

### Login Credentials

**Standard Login:**
- Username: `admin`
- Password: set during initial deployment (see DEPLOYMENT.md)

**PIN Login:**
- Select user from the PIN screen, enter your assigned PIN

---

## Google Maps Setup

The application uses Google Maps API for Eircode address resolution and address autocomplete.

### Required APIs
Enable these APIs in [Google Cloud Console](https://console.cloud.google.com/google/maps-apis):
- **Maps JavaScript API** — Map rendering
- **Geocoding API** — Eircode to address resolution
- **Places API** — Address autocomplete & text search

### API Key Configuration
1. Create an API key in Google Cloud Console
2. For **development**: Set restriction to "None" or add `http://localhost:5001/*`
3. For **production**: Restrict by HTTP referrer to your domain
4. Set the key in `backend/.env` → `GOOGLE_MAPS_API_KEY`
5. Set the same key in `frontend/BurgerPOS/Components/App.razor` (line 30)

### Eircode Lookup Strategy
The system uses a multi-strategy approach for resolving Irish Eircodes:
1. **Google Geocoding API** — Returns exact street addresses when available
2. **Nominatim Reverse Geocoding** — Free fallback using OpenStreetMap data
3. **Eircode Prefix Map** — 100+ area codes mapped to cities (last resort)

---

## Application Routes

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Phone line selector |
| `/login` | Login | Authentication |
| `/order/{customerId}/{orderType}/{phoneLine}` | Order Creation | Main order builder |
| `/ordenes` | Order History | Search and manage orders |
| `/cocina` | Kitchen Display | Real-time kitchen queue |
| `/dashboard` | Dashboard | Sales analytics |
| `/cash` | Cash Register | Session management |
| `/tables` | Tables | Table management |
| `/print-preview/{orderId}` | Print Preview | Ticket preview |
| `/admin/products` | Product Admin | Catalog management |
| `/admin/categories` | Category Admin | Category management |

---

## Development Commands

### Docker
```bash
# Start/stop services
docker compose up -d
docker compose down

# View logs
docker compose logs -f
docker compose logs -f backend

# Rebuild after changes
docker compose up -d --build

# Rebuild specific service
docker compose up -d --build backend
```

### Database
```bash
# Connect to PostgreSQL
docker compose exec db psql -U postgres -d burger_pos

# Backup/restore
docker compose exec db pg_dump -U postgres burger_pos > backup.sql
docker compose exec -T db psql -U postgres burger_pos < backup.sql
```

---

## API Overview

**Total:** 45+ endpoints across 12 routers

| Router | Prefix | Endpoints | Description |
|--------|--------|-----------|-------------|
| **auth** | `/api/auth` | 6 | Login, PIN, profile, verify |
| **customers** | `/api/customers` | 5 | CRUD, search |
| **orders** | `/api/orders` | 4 | Create, list, get, update status |
| **products** | `/api/products` | 5 | CRUD operations |
| **categories** | `/api/categories` | 4 | CRUD operations |
| **tables** | `/api/tables` | 3 | List, create, update status |
| **modifiers** | `/api/modifiers` | 3 | List, create, update |
| **reports** | `/api/reports` | 3 | Daily sales, top products, revenue |
| **cash_register** | `/api/cash` | 7 | Sessions, payments, summaries |
| **geocoding** | `/api/geocoding` | 2 | Eircode lookup, delivery fee |
| **audit** | `/api/audit` | 2 | Security event logging |
| **uploads** | `/api/uploads` | 1 | File uploads |

See [docs/API.md](./docs/API.md) for complete API reference.

---

## Security Features

- JWT authentication with 24-hour expiration
- Bcrypt password hashing (12 rounds)
- Environment-based secrets management
- CORS whitelisting
- Role-based access control
- Parameterized SQL queries
- HTTPS ready (Cloudflare SSL)
- API docs disabled in production
- Audit logging via RabbitMQ
- IP tracking on authentication events

### Best Practices
- Never commit `.env` files
- Change default admin password immediately
- Restrict Google Maps API key by domain/IP in production
- Use strong secrets: `openssl rand -hex 32`
- Enable firewall rules for database access

---

## Production Deployment

**Architecture:** Cloudflare CDN → Nginx → Docker Containers → PostgreSQL

### Production Files
- `docker-compose.prod.example.yml` — Production template
- `frontend/BurgerPOS/Dockerfile` — Multi-stage .NET build
- `backend/Dockerfile` — 4 Uvicorn workers
- `nginx/nginx.conf` — Reverse proxy
- `DEPLOYMENT.md` — Complete guide

### Quick Production Setup
```bash
cp docker-compose.prod.example.yml docker-compose.prod.yml
nano backend/.env  # Set ENV=production, update secrets
docker compose -f docker-compose.prod.yml up -d
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions.

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/API.md](./docs/API.md) | API reference with examples |
| [docs/USER_MANUAL.md](./docs/USER_MANUAL.md) | Staff training guide |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Production deployment guide |

---

## Troubleshooting

### Common Issues

**Frontend container exits:**
```bash
docker compose logs frontend
docker compose up -d --build frontend
```

**Database connection refused:**
```bash
docker compose ps db
docker compose logs db
docker compose restart db
```

**API returns 401 Unauthorized:**
- Token expired (24-hour expiration)
- Check Authorization header: `Bearer <token>`
- Re-login for fresh token

**Eircode lookup not working:**
- Set `GOOGLE_MAPS_API_KEY` in `backend/.env`
- Enable Geocoding API and Places API in Google Cloud Console
- For development: set API key restriction to "None"
- For production: add your domain to allowed HTTP referrers

**Google Maps not loading:**
- Verify API key in `App.razor` matches `backend/.env`
- Enable Maps JavaScript API in Google Cloud Console
- Check browser console for `RefererNotAllowedMapError` (fix key restrictions)

**RabbitMQ connection issues:**
```bash
docker compose restart rabbitmq
docker compose logs rabbitmq
```

---

## License

This project is for educational purposes.

---

## Support

- **GitHub Issues:** https://github.com/gersonrivera27/STACKPOS/issues
- **Documentation:** See [docs/](./docs/) folder

---

**Built for the restaurant industry** 🍔
