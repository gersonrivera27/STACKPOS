# StackPOS User Manual

Staff training guide for the StackPOS Point of Sale system.

---

## Table of Contents

1. [Login](#1-login)
2. [Home Page](#2-home-page)
3. [Creating an Order](#3-creating-an-order)
4. [Order History](#4-order-history)
5. [Printing Tickets](#5-printing-tickets)

---

## 1. Login

Access the system at: `http://localhost:5001`

<!-- TODO: Add screenshot of login page -->
![Login Page](./screenshots/login.png)

**Steps:**
1. Enter your **username** (e.g., `admin`)
2. Enter your **password** (e.g., `admin123`)
3. Click **"Iniciar Sesión"** (Login)

> **Note:** If you forget your password, contact your administrator.

---

## 2. Home Page

After login, you'll see the main dashboard with phone lines.

<!-- TODO: Add screenshot of home page -->
![Home Page](./screenshots/home.png)

**Features:**
- **Phone Lines (1-4)**: Each tab represents a phone line for tracking concurrent calls
- **Collection Button**: Start a pickup/takeaway order
- **Delivery Button**: Start a delivery order
- **Customer Search**: Opens modal to find existing customers

**To Start an Order:**
1. Select a phone line (Line 1, 2, 3, or 4)
2. Search for customer by phone number, or create new
3. Choose **Collection** or **Delivery**
4. You'll be redirected to the order creation page

---

## 3. Creating an Order

The order creation page lets you build customer orders.

<!-- TODO: Add screenshot of order creation page -->
![Order Creation](./screenshots/order_creation.png)

### Left Panel - Products
- **Category Tabs**: Click tabs to browse product categories (Burgers, Sides, Drinks, etc.)
- **Product Cards**: Click a product to add it to the cart
- **Images & Prices**: Each product shows its picture and price

### Right Panel - Cart
- **Cart Items**: Shows all items added to the order
- **Quantity Controls**: Use +/- buttons to adjust quantities
- **Special Instructions**: Click on an item to add notes (e.g., "No onions")
- **Totals**: Displays subtotal, tax (13.5% VAT), and total

### Actions
| Button | Action |
|--------|--------|
| **Send to Kitchen** | Saves order with status "Preparing" and prints kitchen ticket |
| **Pay** | Opens payment modal to complete the order |
| **Clear Cart** | Removes all items from cart |

**Workflow:**
1. Browse categories and click products to add them
2. Adjust quantities if needed
3. Add special instructions for any item
4. Click **"Send to Kitchen"** to submit
5. Complete payment when customer pays

---

## 4. Order History

View and manage all past orders.

<!-- TODO: Add screenshot of order history page -->
![Order History](./screenshots/order_history.png)

### Layout
- **Left Side**: Order list with filters
- **Right Side**: Selected order ticket preview

### Filters
| Filter | Description |
|--------|-------------|
| Order ID | Search by order number (e.g., ORD-2026...) |
| Phone | Search by customer phone |
| Status | Filter by: pending, preparing, completed, cancelled |

### Order Statuses
| Status | Meaning |
|--------|---------|
| 🟡 Pending | Order received, not yet started |
| 🔵 Preparing | Kitchen is working on it |
| 🟢 Completed | Order finished and paid |
| 🔴 Cancelled | Order was cancelled |

### Actions
- **Click an order row** to view its details on the right
- **Pay Button**: Open payment modal for unpaid orders
- **Print Button**: Navigate to print preview

---

## 5. Printing Tickets

Control which printers receive the ticket.

<!-- TODO: Add screenshot of print preview page -->
![Print Preview](./screenshots/print_preview.png)

### Printer Stations
| Station | Purpose |
|---------|---------|
| **Kitchen** | Full order ticket for food preparation |
| **Bar** | Drinks only |
| **Customer Copy** | Receipt for customer |

### Print Options
- **Print Full**: Prints all items in the order
- **Print Last Edit**: Prints only recently added items (for order modifications)

### How to Print
1. Select printer station (Kitchen, Bar, or Customer)
2. Review the ticket preview on the right
3. Click **Print** button
4. Browser print dialog will open
5. Select your printer and confirm

> **Tip:** For thermal printers, set paper size to 80mm and disable headers/footers.

---

## Quick Reference

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| Enter | Submit forms |
| Escape | Close modals |

### Common Tasks

**Create a new customer:**
1. Home page → Search customer → "Not found"
2. Click "Create New Customer"
3. Fill in phone, name, address
4. Use map to verify address location
5. Save

**Apply a discount:**
1. Only admins can apply discounts
2. Contact manager if discount needed

**Cancel an order:**
1. Go to Order History
2. Select the order
3. Change status to "Cancelled"

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't login | Check username/password. Contact admin if locked out. |
| Products not loading | Check backend connection. Refresh page. |
| Print not working | Verify printer is connected. Check browser print settings. |
| Map not showing | Google Maps API key may be missing. Contact admin. |

---

## Support

For technical support, contact your system administrator.

**System Requirements:**
- Modern web browser (Chrome, Firefox, Edge)
- Network connection to server
- For printing: Network-connected printer
