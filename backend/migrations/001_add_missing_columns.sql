-- =============================================================
-- Migration 001: Add missing columns and tables
-- =============================================================
-- Safe to run multiple times (uses IF NOT EXISTS / ADD COLUMN IF NOT EXISTS)
-- Run with:
--   docker cp backend/migrations/001_add_missing_columns.sql burger-db:/tmp/
--   docker exec burger-db psql -U postgres -d burger_pos -f /tmp/001_add_missing_columns.sql
-- =============================================================

-- -----------------------------------------------------------
-- 1. categories: add missing columns
-- -----------------------------------------------------------
ALTER TABLE categories
    ADD COLUMN IF NOT EXISTS description TEXT,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- -----------------------------------------------------------
-- 2. products: add missing `updated_at` column
-- -----------------------------------------------------------
ALTER TABLE products
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Trigger to auto-update updated_at on products
CREATE OR REPLACE FUNCTION update_product_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_product_updated_at ON products;
CREATE TRIGGER trigger_update_product_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_product_updated_at();

-- -----------------------------------------------------------
-- 3. tables: add missing x, y position columns
-- -----------------------------------------------------------
ALTER TABLE tables
    ADD COLUMN IF NOT EXISTS x INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS y INTEGER DEFAULT 0;

-- -----------------------------------------------------------
-- 4. orders: fix NOT NULL constraint + add missing columns
-- -----------------------------------------------------------
-- customer_id is no longer required (code uses customer_name directly)
ALTER TABLE orders ALTER COLUMN customer_id DROP NOT NULL;

ALTER TABLE orders
    ADD COLUMN IF NOT EXISTS order_number   VARCHAR(20),
    ADD COLUMN IF NOT EXISTS table_id       INTEGER REFERENCES tables(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS user_id        INTEGER REFERENCES users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS cash_session_id INTEGER,
    ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50) DEFAULT 'cash',
    ADD COLUMN IF NOT EXISTS completed_at   TIMESTAMP,
    ADD COLUMN IF NOT EXISTS customer_name  VARCHAR(255),
    ADD COLUMN IF NOT EXISTS discount       DECIMAL(10, 2) DEFAULT 0;

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_orders_table        ON orders(table_id);
CREATE INDEX IF NOT EXISTS idx_orders_user         ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);

-- -----------------------------------------------------------
-- 4b. order_items: add missing columns
-- -----------------------------------------------------------
ALTER TABLE order_items
    ADD COLUMN IF NOT EXISTS unit_price           DECIMAL(10, 2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS special_instructions TEXT,
    ADD COLUMN IF NOT EXISTS created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- -----------------------------------------------------------
-- 4c. order_item_modifiers: create table if not exists
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_item_modifiers (
    id            SERIAL PRIMARY KEY,
    order_item_id INTEGER NOT NULL REFERENCES order_items(id) ON DELETE CASCADE,
    modifier_id   INTEGER NOT NULL REFERENCES modifiers(id) ON DELETE CASCADE,
    price         DECIMAL(10, 2) DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_oim_order_item ON order_item_modifiers(order_item_id);
CREATE INDEX IF NOT EXISTS idx_oim_modifier   ON order_item_modifiers(modifier_id);

-- -----------------------------------------------------------
-- 5. cash_sessions: create table with ALL columns used by code
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cash_sessions (
    id                SERIAL PRIMARY KEY,
    user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status            VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    opening_amount    DECIMAL(10, 2) NOT NULL DEFAULT 0,
    closing_amount    DECIMAL(10, 2),
    expected_amount   DECIMAL(10, 2),
    difference        DECIMAL(10, 2),
    total_sales       DECIMAL(10, 2) DEFAULT 0,
    total_cash_sales  DECIMAL(10, 2) DEFAULT 0,
    total_card_sales  DECIMAL(10, 2) DEFAULT 0,
    total_cash        DECIMAL(10, 2) DEFAULT 0,
    total_card        DECIMAL(10, 2) DEFAULT 0,
    total_tips        DECIMAL(10, 2) DEFAULT 0,
    orders_count      INTEGER DEFAULT 0,
    notes             TEXT,
    opened_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at         TIMESTAMP
);

-- If table already existed from migration run, add missing columns
ALTER TABLE cash_sessions
    ADD COLUMN IF NOT EXISTS expected_amount  DECIMAL(10, 2),
    ADD COLUMN IF NOT EXISTS difference       DECIMAL(10, 2),
    ADD COLUMN IF NOT EXISTS total_cash_sales DECIMAL(10, 2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS total_card_sales DECIMAL(10, 2) DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_cash_sessions_user   ON cash_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_cash_sessions_status ON cash_sessions(status);

-- Add FK from orders to cash_sessions now that the table exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_orders_cash_session'
    ) THEN
        ALTER TABLE orders
            ADD CONSTRAINT fk_orders_cash_session
            FOREIGN KEY (cash_session_id) REFERENCES cash_sessions(id) ON DELETE SET NULL;
    END IF;
END $$;

-- -----------------------------------------------------------
-- 6. payments: create table if not exists
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
    id              SERIAL PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    cash_session_id INTEGER REFERENCES cash_sessions(id) ON DELETE SET NULL,
    payment_type    VARCHAR(20) NOT NULL CHECK (payment_type IN ('cash', 'card', 'mixed')),
    total_amount    DECIMAL(10, 2) NOT NULL DEFAULT 0,
    cash_amount     DECIMAL(10, 2) NOT NULL DEFAULT 0,
    card_amount     DECIMAL(10, 2) NOT NULL DEFAULT 0,
    tip_amount      DECIMAL(10, 2) NOT NULL DEFAULT 0,
    change_amount   DECIMAL(10, 2) NOT NULL DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payments_order   ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_session ON payments(cash_session_id);

-- -----------------------------------------------------------
-- 7. audit_logs: create if not exists (for audit_middleware)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    username    VARCHAR(150),
    action      VARCHAR(100) NOT NULL,
    resource    VARCHAR(100),
    resource_id VARCHAR(50),
    ip_address  VARCHAR(45),
    details     JSONB,
    status_code INTEGER,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user    ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action  ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);

-- -----------------------------------------------------------
-- Done
-- -----------------------------------------------------------
\echo '✅ Migration 001 completed successfully'
