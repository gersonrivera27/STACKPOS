-- ============================================
-- BURGER POS DATABASE SCHEMA
-- ============================================

-- Tabla de Clientes
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(200),
    
    -- Dirección
    address_line1 VARCHAR(300),
    address_line2 VARCHAR(300),
    city VARCHAR(100) DEFAULT 'Drogheda',
    county VARCHAR(100) DEFAULT 'Louth',
    eircode VARCHAR(10),
    country VARCHAR(100) DEFAULT 'Ireland',
    
    -- Coordenadas para delivery
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Metadata
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(10, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_customers_eircode ON customers(eircode);
CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);

-- Datos de ejemplo
INSERT INTO customers (phone, name, email, address_line1, city, eircode) VALUES
('0871234567', 'John Doe', 'john@example.com', '123 Main Street', 'Drogheda', 'A92 X7Y8'),
('0879876543', 'Jane Smith', 'jane@example.com', '45 High Street', 'Drogheda', 'A92 K3L9')
ON CONFLICT (phone) DO NOTHING;

-- ============================================
-- Tabla de Categorías
-- ============================================
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

-- Índices para categorías
CREATE INDEX IF NOT EXISTS idx_categories_active ON categories(is_active);
CREATE INDEX IF NOT EXISTS idx_categories_sort ON categories(sort_order);

-- Datos de ejemplo
INSERT INTO categories (name, sort_order) VALUES
('Burgers', 1),
('Sides', 2),
('Drinks', 3),
('Desserts', 4)
ON CONFLICT (name) DO NOTHING;

-- ============================================
-- Tabla de Productos
-- ============================================
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    price DECIMAL(10, 2) NOT NULL,
    description TEXT,
    image_url VARCHAR(500),
    is_available BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    stock_quantity INTEGER DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para productos
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_available ON products(is_available);
CREATE INDEX IF NOT EXISTS idx_products_sort ON products(sort_order);

-- Datos de ejemplo
INSERT INTO products (name, category_id, price, description, sort_order) VALUES
-- Burgers
('Classic Burger', 1, 8.50, 'Beef patty, lettuce, tomato, onion', 1),
('Cheeseburger', 1, 9.50, 'Classic burger with cheddar cheese', 2),
('Bacon Burger', 1, 10.50, 'Beef patty with crispy bacon and cheese', 3),
('Double Burger', 1, 12.00, 'Two beef patties, double cheese', 4),
('Chicken Burger', 1, 9.00, 'Crispy chicken fillet, mayo, lettuce', 5),
('Veggie Burger', 1, 8.00, 'Plant-based patty, fresh vegetables', 6),

-- Sides
('Fries', 2, 3.50, 'Crispy golden fries', 1),
('Onion Rings', 2, 4.00, 'Breaded and fried onion rings', 2),
('Chicken Nuggets', 2, 5.50, '6 pieces of chicken nuggets', 3),
('Mozzarella Sticks', 2, 5.00, 'Breaded mozzarella sticks', 4),
('Coleslaw', 2, 3.00, 'Fresh coleslaw', 5),

-- Drinks
('Coke', 3, 2.50, '330ml can', 1),
('Diet Coke', 3, 2.50, '330ml can', 2),
('Sprite', 3, 2.50, '330ml can', 3),
('Fanta', 3, 2.50, '330ml can', 4),
('Water', 3, 1.50, '500ml bottle', 5),
('Milkshake', 3, 4.50, 'Chocolate, vanilla, or strawberry', 6),

-- Desserts
('Ice Cream', 4, 3.50, 'Two scoops', 1),
('Brownie', 4, 4.00, 'Chocolate brownie with ice cream', 2),
('Apple Pie', 4, 3.50, 'Warm apple pie', 3)
ON CONFLICT DO NOTHING;

-- ============================================
-- Tabla de Órdenes
-- ============================================
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    order_type VARCHAR(20) NOT NULL CHECK (order_type IN ('delivery', 'takeout', 'collection')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'preparing', 'ready', 'completed', 'cancelled')),
    
    -- Montos
    subtotal DECIMAL(10, 2) NOT NULL DEFAULT 0,
    tax DECIMAL(10, 2) NOT NULL DEFAULT 0,
    delivery_fee DECIMAL(10, 2) NOT NULL DEFAULT 0,
    total DECIMAL(10, 2) NOT NULL,
    
    -- Metadata
    notes TEXT,
    phone_line INTEGER CHECK (phone_line BETWEEN 1 AND 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para órdenes
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_phone_line ON orders(phone_line);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_type ON orders(order_type);

-- ============================================
-- Tabla de Items de Orden
-- ============================================
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    notes TEXT
);

-- Índices para items de orden
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);

-- ============================================
-- Tabla de Modificadores (Opcional)
-- ============================================
CREATE TABLE IF NOT EXISTS modifiers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

-- Índices para modificadores
CREATE INDEX IF NOT EXISTS idx_modifiers_active ON modifiers(is_active);

-- Datos de ejemplo
INSERT INTO modifiers (name, price) VALUES
('Extra Cheese', 1.00),
('Extra Bacon', 1.50),
('No Onions', 0.00),
('No Pickles', 0.00),
('Extra Sauce', 0.50)
ON CONFLICT DO NOTHING;

-- ============================================
-- Tabla de Mesas (Opcional)
-- ============================================
CREATE TABLE IF NOT EXISTS tables (
    id SERIAL PRIMARY KEY,
    table_number INTEGER NOT NULL UNIQUE,
    is_occupied BOOLEAN DEFAULT FALSE
);

-- Datos de ejemplo
INSERT INTO tables (table_number) VALUES
(1), (2), (3), (4), (5), (6), (7), (8), (9), (10)
ON CONFLICT (table_number) DO NOTHING;

-- ============================================
-- TRIGGERS
-- ============================================

-- Trigger para actualizar updated_at en customers
CREATE OR REPLACE FUNCTION update_customer_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_customer_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_updated_at();

-- Trigger para actualizar updated_at en orders
CREATE OR REPLACE FUNCTION update_order_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_order_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_order_updated_at();

-- Trigger para actualizar total_orders y total_spent del cliente
CREATE OR REPLACE FUNCTION update_customer_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT' AND NEW.status = 'completed') OR 
       (TG_OP = 'UPDATE' AND OLD.status != 'completed' AND NEW.status = 'completed') THEN
        UPDATE customers
        SET total_orders = total_orders + 1,
            total_spent = total_spent + NEW.total
        WHERE id = NEW.customer_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_customer_stats
    AFTER INSERT OR UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_stats();

-- ============================================
-- COMENTARIOS FINALES
-- ============================================
COMMENT ON TABLE customers IS 'Tabla de clientes del restaurante';
COMMENT ON TABLE categories IS 'Categorías de productos (Burgers, Sides, etc)';
COMMENT ON TABLE products IS 'Productos disponibles en el menú';
COMMENT ON TABLE orders IS 'Órdenes de clientes';
COMMENT ON TABLE order_items IS 'Items individuales de cada orden';
COMMENT ON TABLE modifiers IS 'Modificadores para productos (extras, sin ingredientes)';
COMMENT ON TABLE tables IS 'Mesas del restaurante';
-- ============================================
-- Tabla de Usuarios (Admin/Staff)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(200) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'staff',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Índices para usuarios
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Usuario Admin por defecto (password: BurgerAdmin2025!)
-- IMPORTANTE: Cambiar esta contraseña después del primer login
INSERT INTO users (username, email, hashed_password, full_name, role)
VALUES ('admin', 'admin@burgerpos.com', '$2b$12$jUipsQQGhPKJ1TBl4fF/DuBwSwDdw1yRkE7SxyVjIscSh2Ie/JuXi', 'System Admin', 'admin')
ON CONFLICT (username) DO NOTHING;

