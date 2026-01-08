-- ============================================
-- 采购物料成本清单模块 - SQLite 迁移文件
-- 创建日期: 2025-01-15
-- 说明: 添加采购物料成本清单表（采购部维护的标准件成本信息）
-- ============================================

-- 采购物料成本清单表
CREATE TABLE IF NOT EXISTS purchase_material_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_code VARCHAR(50),
    material_name VARCHAR(200) NOT NULL,
    specification VARCHAR(500),
    brand VARCHAR(100),
    unit VARCHAR(20) DEFAULT '件',
    material_type VARCHAR(50),
    is_standard_part BOOLEAN DEFAULT 1,
    unit_cost DECIMAL(12, 4) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    supplier_id INTEGER,
    supplier_name VARCHAR(200),
    purchase_date DATE,
    purchase_order_no VARCHAR(50),
    purchase_quantity DECIMAL(10, 4),
    lead_time_days INTEGER,
    is_active BOOLEAN DEFAULT 1,
    match_priority INTEGER DEFAULT 0,
    match_keywords TEXT,
    usage_count INTEGER DEFAULT 0,
    last_used_at DATETIME,
    remark TEXT,
    submitted_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (submitted_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_material_code ON purchase_material_costs(material_code);
CREATE INDEX IF NOT EXISTS idx_material_name ON purchase_material_costs(material_name);
CREATE INDEX IF NOT EXISTS idx_material_type ON purchase_material_costs(material_type);
CREATE INDEX IF NOT EXISTS idx_is_standard ON purchase_material_costs(is_standard_part);
CREATE INDEX IF NOT EXISTS idx_is_active ON purchase_material_costs(is_active);
CREATE INDEX IF NOT EXISTS idx_match_priority ON purchase_material_costs(match_priority);
