# StackPOS API Reference

Base URL: `http://localhost:8000/api`

## Authentication

All endpoints (except `/auth/login`) require a JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

---

## Auth Endpoints

### POST /auth/login
Authenticate user and get JWT token.

**Request Body:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### GET /auth/me
Get current authenticated user.

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "admin",
  "role": "admin",
  "is_active": true
}
```

---

## Customers Endpoints

### GET /customers
List all customers with optional search.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| search | string | Search by name or phone |
| limit | int | Max results (default: 50) |

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "phone": "0871234567",
    "name": "John Doe",
    "email": "john@email.com",
    "address_line1": "123 Main St",
    "city": "Dublin",
    "eircode": "D01ABC1",
    "latitude": 53.3498,
    "longitude": -6.2603
  }
]
```

### GET /customers/search-by-phone/{phone}
Find customer by exact phone number.

**Response (200 OK):** Single customer object or 404.

### POST /customers
Create new customer.

**Request Body:**
```json
{
  "phone": "0871234567",
  "name": "John Doe",
  "email": "john@email.com",
  "address_line1": "123 Main St",
  "city": "Dublin",
  "eircode": "D01ABC1",
  "latitude": 53.3498,
  "longitude": -6.2603
}
```

### PUT /customers/{id}
Update existing customer.

---

## Products & Categories

### GET /products
List all products.

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Classic Burger",
    "price": 9.99,
    "category_id": 1,
    "is_available": true,
    "image_url": "/images/classic-burger.jpg"
  }
]
```

### GET /categories
List all categories.

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Burgers",
    "description": "Our signature burgers"
  }
]
```

---

## Orders Endpoints

### GET /orders
List orders with optional filters.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | pending, preparing, completed, cancelled |
| order_type | string | collection, delivery, dine_in |
| limit | int | Max results (default: 50) |

### GET /orders/{id}
Get order with all items.

**Response (200 OK):**
```json
{
  "id": 1,
  "order_number": "ORD-20260120143000",
  "customer_name": "John Doe",
  "order_type": "delivery",
  "status": "preparing",
  "subtotal": 19.98,
  "tax": 2.70,
  "total": 22.68,
  "items": [
    {
      "id": 1,
      "product_id": 1,
      "product_name": "Classic Burger",
      "quantity": 2,
      "unit_price": 9.99,
      "subtotal": 19.98,
      "special_instructions": "No onions"
    }
  ],
  "created_at": "2026-01-20T14:30:00Z"
}
```

### POST /orders
Create new order with items.

**Request Body:**
```json
{
  "customer_name": "John Doe",
  "order_type": "delivery",
  "items": [
    {
      "product_id": 1,
      "quantity": 2,
      "special_instructions": "No onions"
    }
  ],
  "notes": "Ring doorbell twice"
}
```

### PATCH /orders/{id}/status
Update order status.

**Request Body:**
```json
{
  "status": "completed"
}
```

**Valid statuses:** `pending`, `preparing`, `completed`, `cancelled`

---

## Tables Endpoints

### GET /tables
List all tables.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | available, occupied, reserved |

### POST /tables
Create new table.

**Request Body:**
```json
{
  "table_number": 5,
  "capacity": 4,
  "status": "available"
}
```

### PATCH /tables/{id}/status
Update table status. Valid: `available`, `occupied`, `reserved`

---

## Modifiers Endpoints

### GET /modifiers
List all product modifiers.

### POST /modifiers
Create new modifier.

**Request Body:**
```json
{
  "name": "Extra Cheese",
  "price": 1.50,
  "modifier_type": "topping"
}
```

---

## Reports Endpoints

### GET /reports/daily-sales
Get daily sales summary.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| report_date | date | YYYY-MM-DD (default: today) |

**Response (200 OK):**
```json
{
  "date": "2026-01-20",
  "summary": {
    "total_orders": 45,
    "total_sales": 892.50,
    "average_ticket": 19.83,
    "completed_orders": 42,
    "cancelled_orders": 3
  },
  "by_order_type": [
    {"order_type": "delivery", "count": 25, "total": 520.00},
    {"order_type": "collection", "count": 17, "total": 372.50}
  ]
}
```

### GET /reports/top-products
Get best selling products.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| date_from | date | Start date |
| date_to | date | End date |
| limit | int | Max products (default: 10) |

### GET /reports/revenue-by-period
Get revenue breakdown.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| date_from | date | Required |
| date_to | date | Required |
| group_by | string | day, week, or month |

---

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error message here"
}
```

**Common Status Codes:**
| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing/invalid token |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Check request body |
