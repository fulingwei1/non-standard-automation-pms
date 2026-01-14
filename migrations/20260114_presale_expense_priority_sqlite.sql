-- ============================================
-- 售前费用与优先级管理模块 - SQLite 迁移文件
-- 创建日期: 2026-01-14
-- 说明: 添加售前费用表，扩展线索和商机表添加优先级字段
-- ============================================

-- 1. 创建售前费用表
CREATE TABLE IF NOT EXISTS presale_expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    project_code VARCHAR(50),
    project_name VARCHAR(200),
    lead_id INTEGER,
    opportunity_id INTEGER,
    expense_type VARCHAR(20) NOT NULL,
    expense_category VARCHAR(50) NOT NULL,
    amount NUMERIC(14, 2) NOT NULL,
    labor_hours NUMERIC(10, 2),
    hourly_rate NUMERIC(10, 2),
    user_id INTEGER,
    user_name VARCHAR(50),
    department_id INTEGER,
    department_name VARCHAR(100),
    salesperson_id INTEGER,
    salesperson_name VARCHAR(50),
    expense_date DATE NOT NULL,
    description TEXT,
    loss_reason VARCHAR(50),
    loss_reason_detail TEXT,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (lead_id) REFERENCES leads(id),
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (salesperson_id) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_presale_expense_project ON presale_expenses(project_id);
CREATE INDEX IF NOT EXISTS idx_presale_expense_lead ON presale_expenses(lead_id);
CREATE INDEX IF NOT EXISTS idx_presale_expense_opportunity ON presale_expenses(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_presale_expense_type ON presale_expenses(expense_type);
CREATE INDEX IF NOT EXISTS idx_presale_expense_category ON presale_expenses(expense_category);
CREATE INDEX IF NOT EXISTS idx_presale_expense_date ON presale_expenses(expense_date);
CREATE INDEX IF NOT EXISTS idx_presale_expense_user ON presale_expenses(user_id);
CREATE INDEX IF NOT EXISTS idx_presale_expense_salesperson ON presale_expenses(salesperson_id);
CREATE INDEX IF NOT EXISTS idx_presale_expense_department ON presale_expenses(department_id);

-- 2. 扩展leads表添加优先级字段
-- SQLite不支持ALTER TABLE ADD COLUMN IF NOT EXISTS，需要检查列是否存在
-- 这里直接添加，如果已存在会报错，需要手动处理
ALTER TABLE leads ADD COLUMN priority_score INTEGER;
ALTER TABLE leads ADD COLUMN is_key_lead BOOLEAN DEFAULT 0;
ALTER TABLE leads ADD COLUMN priority_level VARCHAR(10);
ALTER TABLE leads ADD COLUMN importance_level VARCHAR(10);
ALTER TABLE leads ADD COLUMN urgency_level VARCHAR(10);

CREATE INDEX IF NOT EXISTS idx_leads_priority_score ON leads(priority_score);
CREATE INDEX IF NOT EXISTS idx_leads_is_key ON leads(is_key_lead);
CREATE INDEX IF NOT EXISTS idx_leads_priority_level ON leads(priority_level);

-- 3. 扩展opportunities表添加优先级字段
ALTER TABLE opportunities ADD COLUMN priority_score INTEGER;
ALTER TABLE opportunities ADD COLUMN is_key_opportunity BOOLEAN DEFAULT 0;
ALTER TABLE opportunities ADD COLUMN priority_level VARCHAR(10);

CREATE INDEX IF NOT EXISTS idx_opportunities_priority_score ON opportunities(priority_score);
CREATE INDEX IF NOT EXISTS idx_opportunities_is_key ON opportunities(is_key_opportunity);
CREATE INDEX IF NOT EXISTS idx_opportunities_priority_level ON opportunities(priority_level);
