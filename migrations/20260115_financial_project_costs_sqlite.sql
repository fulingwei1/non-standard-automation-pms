-- ============================================
-- 财务历史项目成本模块 - SQLite 迁移文件
-- 创建日期: 2025-01-15
-- 说明: 添加财务历史项目成本表（财务部维护的非物料成本）
-- ============================================

-- 财务历史项目成本表
CREATE TABLE IF NOT EXISTS financial_project_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    project_code VARCHAR(50),
    project_name VARCHAR(200),
    machine_id INTEGER,
    cost_type VARCHAR(50) NOT NULL,
    cost_category VARCHAR(50) NOT NULL,
    cost_item VARCHAR(200),
    amount DECIMAL(14, 2) NOT NULL,
    tax_amount DECIMAL(12, 2) DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'CNY',
    cost_date DATE NOT NULL,
    cost_month VARCHAR(7),
    description TEXT,
    location VARCHAR(200),
    participants VARCHAR(500),
    purpose VARCHAR(500),
    user_id INTEGER,
    user_name VARCHAR(50),
    hours DECIMAL(10, 2),
    hourly_rate DECIMAL(10, 2),
    source_type VARCHAR(50) DEFAULT 'FINANCIAL_UPLOAD',
    source_no VARCHAR(100),
    invoice_no VARCHAR(100),
    upload_batch_no VARCHAR(50),
    uploaded_by INTEGER NOT NULL,
    is_verified BOOLEAN DEFAULT 0,
    verified_by INTEGER,
    verified_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id),
    FOREIGN KEY (verified_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_financial_cost_project ON financial_project_costs(project_id);
CREATE INDEX IF NOT EXISTS idx_financial_cost_type ON financial_project_costs(cost_type);
CREATE INDEX IF NOT EXISTS idx_financial_cost_category ON financial_project_costs(cost_category);
CREATE INDEX IF NOT EXISTS idx_financial_cost_date ON financial_project_costs(cost_date);
CREATE INDEX IF NOT EXISTS idx_financial_cost_month ON financial_project_costs(cost_month);
CREATE INDEX IF NOT EXISTS idx_financial_cost_upload_batch ON financial_project_costs(upload_batch_no);
