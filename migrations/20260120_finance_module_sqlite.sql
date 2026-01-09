-- ============================================
-- 融资管理模块 - SQLite 迁移文件
-- 创建日期: 2025-01-20
-- 说明: 创建融资管理模块相关表
-- ============================================

-- ============================================
-- 1. 投资方表（需要先创建，因为融资轮次表引用它）
-- ============================================
CREATE TABLE IF NOT EXISTS investors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_code VARCHAR(50) NOT NULL UNIQUE,
    investor_name VARCHAR(200) NOT NULL,
    investor_type VARCHAR(20) NOT NULL,
    
    -- 基本信息
    legal_name VARCHAR(200),
    registration_no VARCHAR(100),
    country VARCHAR(50) DEFAULT '中国',
    region VARCHAR(50),
    address VARCHAR(500),
    
    -- 联系信息
    contact_person VARCHAR(50),
    contact_phone VARCHAR(50),
    contact_email VARCHAR(100),
    website VARCHAR(200),
    
    -- 投资信息
    investment_focus TEXT,
    investment_stage VARCHAR(100),
    typical_ticket_size DECIMAL(15, 2),
    portfolio_companies TEXT,
    
    -- 状态
    is_active BOOLEAN DEFAULT 1,
    is_lead_investor BOOLEAN DEFAULT 0,
    
    -- 备注
    description TEXT,
    notes TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_investor_code ON investors(investor_code);
CREATE INDEX IF NOT EXISTS idx_investor_type ON investors(investor_type);
CREATE INDEX IF NOT EXISTS idx_investor_name ON investors(investor_name);

-- ============================================
-- 2. 融资轮次表
-- ============================================
CREATE TABLE IF NOT EXISTS funding_rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_code VARCHAR(50) NOT NULL UNIQUE,
    round_name VARCHAR(100) NOT NULL,
    round_type VARCHAR(20) NOT NULL,
    round_order INTEGER NOT NULL,
    
    -- 融资信息
    target_amount DECIMAL(15, 2) NOT NULL,
    actual_amount DECIMAL(15, 2) DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'CNY',
    valuation_pre DECIMAL(15, 2),
    valuation_post DECIMAL(15, 2),
    
    -- 时间信息
    launch_date DATE,
    closing_date DATE,
    expected_closing_date DATE,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'PLANNING',
    
    -- 负责人
    lead_investor_id INTEGER,
    lead_investor_name VARCHAR(200),
    responsible_person_id INTEGER,
    responsible_person_name VARCHAR(50),
    
    -- 备注
    description TEXT,
    notes TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (lead_investor_id) REFERENCES investors(id),
    FOREIGN KEY (responsible_person_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_funding_round_code ON funding_rounds(round_code);
CREATE INDEX IF NOT EXISTS idx_funding_round_type ON funding_rounds(round_type);
CREATE INDEX IF NOT EXISTS idx_funding_round_status ON funding_rounds(status);
CREATE INDEX IF NOT EXISTS idx_funding_round_order ON funding_rounds(round_order);

-- ============================================
-- 3. 融资记录表
-- ============================================
CREATE TABLE IF NOT EXISTS funding_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_code VARCHAR(50) NOT NULL UNIQUE,
    
    -- 关联信息
    funding_round_id INTEGER NOT NULL,
    investor_id INTEGER NOT NULL,
    
    -- 投资信息
    investment_amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    share_percentage DECIMAL(8, 4),
    share_count DECIMAL(15, 2),
    price_per_share DECIMAL(10, 4),
    
    -- 时间信息
    commitment_date DATE,
    payment_date DATE,
    actual_payment_date DATE,
    
    -- 付款信息
    payment_method VARCHAR(20),
    payment_status VARCHAR(20) DEFAULT 'PENDING',
    paid_amount DECIMAL(15, 2) DEFAULT 0,
    remaining_amount DECIMAL(15, 2),
    
    -- 合同信息
    contract_no VARCHAR(100),
    contract_date DATE,
    contract_file VARCHAR(500),
    
    -- 状态
    status VARCHAR(20) DEFAULT 'COMMITTED',
    
    -- 备注
    description TEXT,
    notes TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (funding_round_id) REFERENCES funding_rounds(id),
    FOREIGN KEY (investor_id) REFERENCES investors(id)
);

CREATE INDEX IF NOT EXISTS idx_funding_record_round ON funding_records(funding_round_id);
CREATE INDEX IF NOT EXISTS idx_funding_record_investor ON funding_records(investor_id);
CREATE INDEX IF NOT EXISTS idx_funding_record_status ON funding_records(status);
CREATE INDEX IF NOT EXISTS idx_funding_record_payment ON funding_records(payment_status);

-- ============================================
-- 4. 股权结构表
-- ============================================
CREATE TABLE IF NOT EXISTS equity_structures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 关联信息
    funding_round_id INTEGER NOT NULL,
    investor_id INTEGER,
    
    -- 股东信息
    shareholder_name VARCHAR(200) NOT NULL,
    shareholder_type VARCHAR(20) NOT NULL,
    
    -- 股权信息
    share_percentage DECIMAL(8, 4) NOT NULL,
    share_count DECIMAL(15, 2),
    share_class VARCHAR(20),
    
    -- 时间信息
    effective_date DATE NOT NULL,
    
    -- 备注
    description TEXT,
    notes TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (funding_round_id) REFERENCES funding_rounds(id),
    FOREIGN KEY (investor_id) REFERENCES investors(id)
);

CREATE INDEX IF NOT EXISTS idx_equity_round ON equity_structures(funding_round_id);
CREATE INDEX IF NOT EXISTS idx_equity_investor ON equity_structures(investor_id);
CREATE INDEX IF NOT EXISTS idx_equity_type ON equity_structures(shareholder_type);
CREATE INDEX IF NOT EXISTS idx_equity_date ON equity_structures(effective_date);

-- ============================================
-- 5. 融资用途表
-- ============================================
CREATE TABLE IF NOT EXISTS funding_usages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 关联信息
    funding_round_id INTEGER NOT NULL,
    
    -- 用途信息
    usage_category VARCHAR(50) NOT NULL,
    usage_item VARCHAR(200) NOT NULL,
    planned_amount DECIMAL(15, 2) NOT NULL,
    actual_amount DECIMAL(15, 2) DEFAULT 0,
    percentage DECIMAL(5, 2),
    
    -- 时间信息
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'PLANNED',
    
    -- 负责人
    responsible_person_id INTEGER,
    responsible_person_name VARCHAR(50),
    
    -- 备注
    description TEXT,
    notes TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (funding_round_id) REFERENCES funding_rounds(id),
    FOREIGN KEY (responsible_person_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_funding_usage_round ON funding_usages(funding_round_id);
CREATE INDEX IF NOT EXISTS idx_funding_usage_category ON funding_usages(usage_category);
CREATE INDEX IF NOT EXISTS idx_funding_usage_status ON funding_usages(status);
