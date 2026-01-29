-- ============================================
-- SISTEMA DE CAJA - TABLAS ADICIONALES
-- ============================================

-- Tabla de Sesiones de Caja
CREATE TABLE IF NOT EXISTS cash_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    
    -- Montos
    opening_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    closing_amount DECIMAL(10, 2),
    expected_amount DECIMAL(10, 2),
    difference DECIMAL(10, 2),
    
    -- Totales calculados
    total_cash_sales DECIMAL(10, 2) DEFAULT 0,
    total_card_sales DECIMAL(10, 2) DEFAULT 0,
    total_sales DECIMAL(10, 2) DEFAULT 0,
    total_tips DECIMAL(10, 2) DEFAULT 0,
    orders_count INTEGER DEFAULT 0,
    
    -- Metadata
    notes TEXT,
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
);

-- Índices para sesiones de caja
CREATE INDEX IF NOT EXISTS idx_cash_sessions_user ON cash_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_cash_sessions_status ON cash_sessions(status);
CREATE INDEX IF NOT EXISTS idx_cash_sessions_opened_at ON cash_sessions(opened_at);

-- Tabla de Pagos
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    cash_session_id INTEGER REFERENCES cash_sessions(id),
    
    -- Tipo y montos
    payment_type VARCHAR(20) NOT NULL CHECK (payment_type IN ('cash', 'card', 'mixed')),
    total_amount DECIMAL(10, 2) NOT NULL,
    cash_amount DECIMAL(10, 2) DEFAULT 0,
    card_amount DECIMAL(10, 2) DEFAULT 0,
    tip_amount DECIMAL(10, 2) DEFAULT 0,
    change_amount DECIMAL(10, 2) DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para pagos
CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_session ON payments(cash_session_id);
CREATE INDEX IF NOT EXISTS idx_payments_created ON payments(created_at);

-- ============================================
-- TRIGGER: Actualizar totales de sesión de caja
-- ============================================
CREATE OR REPLACE FUNCTION update_cash_session_totals()
RETURNS TRIGGER AS $$
BEGIN
    -- Actualizar totales de la sesión de caja
    IF NEW.cash_session_id IS NOT NULL THEN
        UPDATE cash_sessions
        SET 
            total_cash_sales = total_cash_sales + NEW.cash_amount,
            total_card_sales = total_card_sales + NEW.card_amount,
            total_sales = total_sales + NEW.total_amount,
            total_tips = total_tips + NEW.tip_amount,
            orders_count = orders_count + 1,
            expected_amount = opening_amount + total_cash_sales + NEW.cash_amount + total_tips + NEW.tip_amount
        WHERE id = NEW.cash_session_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_cash_session_totals ON payments;
CREATE TRIGGER trigger_update_cash_session_totals
    AFTER INSERT ON payments
    FOR EACH ROW
    EXECUTE FUNCTION update_cash_session_totals();

-- Comentarios
COMMENT ON TABLE cash_sessions IS 'Sesiones de caja (apertura/cierre)';
COMMENT ON TABLE payments IS 'Pagos registrados para órdenes';
