-- ============================================
-- 报价成本管理模块 - SQLite 迁移文件
-- 创建日期: 2025-01-15
-- 说明: 添加报价成本模板、成本审批、成本历史记录表
-- ============================================

-- 1. 报价成本模板表
CREATE TABLE IF NOT EXISTS quote_cost_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(50) UNIQUE NOT NULL,
    template_name VARCHAR(200) NOT NULL,
    template_type VARCHAR(50),
    equipment_type VARCHAR(50),
    industry VARCHAR(50),
    cost_structure TEXT,  -- JSON格式
    total_cost DECIMAL(12, 2),
    cost_categories TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    usage_count INTEGER DEFAULT 0,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_template_type ON quote_cost_templates(template_type);
CREATE INDEX IF NOT EXISTS idx_equipment_type ON quote_cost_templates(equipment_type);
CREATE INDEX IF NOT EXISTS idx_is_active ON quote_cost_templates(is_active);

-- 2. 报价成本审批表
CREATE TABLE IF NOT EXISTS quote_cost_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id INTEGER NOT NULL,
    quote_version_id INTEGER NOT NULL,
    approval_status VARCHAR(20) DEFAULT 'PENDING',
    approval_level INTEGER DEFAULT 1,
    current_approver_id INTEGER,
    total_price DECIMAL(12, 2),
    total_cost DECIMAL(12, 2),
    gross_margin DECIMAL(5, 2),
    margin_threshold DECIMAL(5, 2) DEFAULT 20.00,
    margin_status VARCHAR(20),
    cost_complete BOOLEAN DEFAULT 0,
    delivery_check BOOLEAN DEFAULT 0,
    risk_terms_check BOOLEAN DEFAULT 0,
    approval_comment TEXT,
    approved_by INTEGER,
    approved_at DATETIME,
    rejected_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quote_id) REFERENCES quotes(id),
    FOREIGN KEY (quote_version_id) REFERENCES quote_versions(id),
    FOREIGN KEY (current_approver_id) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_quote_id ON quote_cost_approvals(quote_id);
CREATE INDEX IF NOT EXISTS idx_approval_status ON quote_cost_approvals(approval_status);

-- 3. 报价成本历史记录表
CREATE TABLE IF NOT EXISTS quote_cost_histories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id INTEGER NOT NULL,
    quote_version_id INTEGER NOT NULL,
    total_price DECIMAL(12, 2),
    total_cost DECIMAL(12, 2),
    gross_margin DECIMAL(5, 2),
    cost_breakdown TEXT,  -- JSON格式
    change_type VARCHAR(50),
    change_reason TEXT,
    changed_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quote_id) REFERENCES quotes(id),
    FOREIGN KEY (quote_version_id) REFERENCES quote_versions(id),
    FOREIGN KEY (changed_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_quote_id ON quote_cost_histories(quote_id);
CREATE INDEX IF NOT EXISTS idx_created_at ON quote_cost_histories(created_at);

-- 4. 扩展 quote_versions 表
-- 添加成本管理相关字段
ALTER TABLE quote_versions ADD COLUMN cost_template_id INTEGER;
ALTER TABLE quote_versions ADD COLUMN cost_breakdown_complete BOOLEAN DEFAULT 0;
ALTER TABLE quote_versions ADD COLUMN margin_warning BOOLEAN DEFAULT 0;

-- 添加外键约束（SQLite不支持ALTER TABLE ADD FOREIGN KEY，需要在应用层处理）
-- FOREIGN KEY (cost_template_id) REFERENCES quote_cost_templates(id)

-- 5. 扩展 quote_items 表
-- 添加成本管理相关字段
ALTER TABLE quote_items ADD COLUMN cost_category VARCHAR(50);
ALTER TABLE quote_items ADD COLUMN cost_source VARCHAR(50);
ALTER TABLE quote_items ADD COLUMN specification TEXT;
ALTER TABLE quote_items ADD COLUMN unit VARCHAR(20);

-- 注释说明
-- quote_cost_templates: 报价成本模板表，存储可复用的成本结构模板
-- quote_cost_approvals: 报价成本审批表，记录成本审批流程和结果
-- quote_cost_histories: 报价成本历史记录表，记录成本变更历史
-- quote_versions扩展: 添加成本模板关联、完整性检查、预警标志
-- quote_items扩展: 添加成本分类、来源、规格、单位等字段








