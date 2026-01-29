# 🍔 StackPOS - Restaurant Point of Sale System

A modern, web-based Point of Sale (POS) system designed for restaurants handling dine-in, takeaway, and delivery orders.

## 🏗️ Architecture

| Layer | Technology |
|-------|------------|
| **Frontend** | .NET 8.0 Blazor Server |
| **Backend** | Python FastAPI |
| **Database** | PostgreSQL 15 |
| **Containerization** | Docker Compose |
| **Maps** | Google Maps API |

## ✅ Implemented Features

### Core POS
- **User Authentication** - JWT-based login with admin/employee roles
- **Customer Management** - Search, create, edit customers with phone/address
- **Product Catalog** - Categories and products with images and prices
- **Order Creation** - Full shopping cart with quantities and special instructions
- **Order History** - Search and filter past orders by ID, phone, or status
- **Payment Processing** - Cash, card, and voucher support with change calculation

### Printing System
- **Print Preview** - Visual ticket preview before printing
- **Multi-Station Support** - Kitchen, Bar, and Customer copy routing
- **Thermal Receipt Styling** - Optimized for receipt printers

### Integrations
- **Google Maps** - Address lookup and geocoding for deliveries
- **Location Coordinates** - Latitude/longitude storage for drivers

## 📁 Project Structure

```
burguer/
├── frontend/              # .NET Blazor Application
│   └── BurgerPOS/
│       ├── Components/
│       │   └── Pages/     # Home, Login, OrderCreation, OrderHistory, PrintPreview
│       └── Services/      # API, Auth, State management
├── backend/               # Python FastAPI
│   └── app/
│       ├── routers/       # auth, customers, orders, products, categories, reports
│       ├── models/        # SQLAlchemy models
│       └── schemas/       # Pydantic schemas
├── docs/                  # Documentation
├── docker-compose.yml
└── SYSTEM_DOCUMENTATION.md
```

## 🚀 Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/gersonrivera27/STACKPOS.git
cd burguer
cp backend/.env.example backend/.env
cp .env.db.example .env.db
```

Edit `backend/.env` and add your Google Maps API key:
```
GOOGLE_MAPS_API_KEY=your_api_key_here
```

### 2. Start Containers

```bash
docker-compose up -d
```

### 3. Access the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5001 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

### Default Login
- **Username:** `admin`
- **Password:** `admin123`

## 📖 Documentation

- [System Documentation](./SYSTEM_DOCUMENTATION.md) - Complete system overview
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment instructions
- [API Reference](./docs/API.md) - Detailed API documentation
- [User Manual](./docs/USER_MANUAL.md) - Staff training guide

## 🛠️ Development Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop and remove containers
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

## 🔐 Security

> ⚠️ **Important**: Never commit `.env` files to version control. API keys and credentials must be managed locally.

## 📋 Roadmap

- [ ] Kitchen Display Screen (KDS)
- [ ] Driver assignment & tracking
- [ ] Inventory management
- [ ] Sales reports & analytics
- [ ] Online ordering portal

## 📄 License

This project is for educational purposes.
