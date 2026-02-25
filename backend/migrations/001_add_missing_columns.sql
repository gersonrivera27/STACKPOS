-- =============================================================
-- Migration 001: Add missing columns and tables
-- =============================================================
-- Safe to run multiple times (uses IF NOT EXISTS / ADD COLUMN IF NOT EXISTS)
-- Run with:
--   docker exec burger-db psql -U postgres -d burger_pos -f /tmp/001_add_missing_columns.sql
-- =============================================================

-- -----------------------------------------------------------
-- 1. categories: add missing `description` column
-- -----------------------------------------------------------
ALTER TABLE categories
    ADD COLUMN IF NOT EXISTS description TEXT;

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
-- 4. orders: add missing columns
-- -----------------------------------------------------------
ALTER TABLE orders
    ADD COLUMN IF NOT EXISTS table_id INTEGER REFERENCES tables(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS cash_session_id INTEGER,
    ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50) DEFAULT 'cash',
    ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS customer_name VARCHAR(255);

-- Index for table_id lookups
CREATE INDEX IF NOT EXISTS idx_orders_table ON orders(table_id);
CREATE INDEX IF NOT EXISTS idx_orders_user  ON orders(user_id);

-- -----------------------------------------------------------
-- 5. cash_sessions: create table if not exists
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cash_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    opening_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    closing_amount DECIMAL(10, 2),
    total_sales DECIMAL(10, 2) DEFAULT 0,
    total_cash DECIMAL(10, 2) DEFAULT 0,
    total_card DECIMAL(10, 2) DEFAULT 0,
    total_tips DECIMAL(10, 2) DEFAULT 0,
    orders_count INTEGER DEFAULT 0,
    notes TEXT,
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cash_sessions_user   ON cash_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_cash_sessions_status ON cash_sessions(status);

-- Add FK from orders to cash_sessions now that the table exists
ALTER TABLE orders
    ADD CONSTRAINT IF NOT EXISTS fk_orders_cash_session
    FOREIGN KEY (cash_session_id) REFERENCES cash_sessions(id) ON DELETE SET NULL;

-- -----------------------------------------------------------
-- 6. audit_logs: create if not exists (for audit_middleware)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    username VARCHAR(150),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    resource_id VARCHAR(50),
    ip_address VARCHAR(45),
    details JSONB,
    status_code INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user    ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action  ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);

-- -----------------------------------------------------------
-- Done
-- -----------------------------------------------------------
\echo '✅ Migration 001 completed successfully'
