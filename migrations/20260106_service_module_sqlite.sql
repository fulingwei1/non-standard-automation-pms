-- Service module migration (SQLite)
-- Targets: customer_communications, customer_satisfactions, knowledge_base
-- Note: service_tickets and service_records tables already exist

PRAGMA foreign_keys = ON;
BEGIN;

-- Customer Communications Table
CREATE TABLE IF NOT EXISTS customer_communications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    communication_no VARCHAR(50) UNIQUE NOT NULL,
    communication_type VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    customer_contact VARCHAR(50),
    customer_phone VARCHAR(20),
    customer_email VARCHAR(100),
    project_code VARCHAR(50),
    project_name VARCHAR(200),
    communication_date DATE NOT NULL,
    communication_time VARCHAR(10),
    duration INTEGER,
    location VARCHAR(200),
    topic VARCHAR(50) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    follow_up_required BOOLEAN DEFAULT 0,
    follow_up_task TEXT,
    follow_up_due_date DATE,
    follow_up_status VARCHAR(20),
    tags TEXT,  -- JSON format
    importance VARCHAR(10) DEFAULT '中',
    created_by INTEGER NOT NULL,
    created_by_name VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_communication_customer ON customer_communications(customer_name);
CREATE INDEX IF NOT EXISTS idx_communication_date ON customer_communications(communication_date);

-- Customer Satisfactions Table
CREATE TABLE IF NOT EXISTS customer_satisfactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    survey_no VARCHAR(50) UNIQUE NOT NULL,
    survey_type VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    customer_contact VARCHAR(50),
    customer_email VARCHAR(100),
    customer_phone VARCHAR(20),
    project_code VARCHAR(50),
    project_name VARCHAR(200),
    survey_date DATE NOT NULL,
    send_date DATE,
    send_method VARCHAR(20),
    deadline DATE,
    status VARCHAR(20) DEFAULT 'DRAFT' NOT NULL,
    response_date DATE,
    overall_score NUMERIC(3, 1),
    scores TEXT,  -- JSON format
    feedback TEXT,
    suggestions TEXT,
    created_by INTEGER NOT NULL,
    created_by_name VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_satisfaction_customer ON customer_satisfactions(customer_name);
CREATE INDEX IF NOT EXISTS idx_satisfaction_date ON customer_satisfactions(survey_date);

-- Knowledge Base Table
CREATE TABLE IF NOT EXISTS knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_no VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    tags TEXT,  -- JSON format
    is_faq BOOLEAN DEFAULT 0,
    is_featured BOOLEAN DEFAULT 0,
    status VARCHAR(20) DEFAULT 'DRAFT',
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    author_id INTEGER NOT NULL,
    author_name VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_base(category);
CREATE INDEX IF NOT EXISTS idx_kb_status ON knowledge_base(status);
CREATE INDEX IF NOT EXISTS idx_kb_faq ON knowledge_base(is_faq);

COMMIT;



