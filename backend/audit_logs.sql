-- Audit logs initialization placeholder
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    event VARCHAR(50),
    username VARCHAR(100),
    user_id INTEGER,
    ip_address VARCHAR(50),
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
