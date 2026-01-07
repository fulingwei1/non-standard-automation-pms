
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_no VARCHAR(50) UNIQUE NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    payment_type VARCHAR(20),  -- RECEIVE/PAY
    status VARCHAR(20) DEFAULT 'PENDING',
    payment_date DATE,
    payer_name VARCHAR(100),
    payee_name VARCHAR(100),
    bank_account VARCHAR(100),
    transaction_no VARCHAR(100),
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
