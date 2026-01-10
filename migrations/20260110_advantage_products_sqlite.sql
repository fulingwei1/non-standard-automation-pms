-- 优势产品管理迁移脚本 (SQLite)
-- 日期: 2026-01-10
-- 描述: 创建优势产品类别和优势产品表，用于管理公司主推产品

-- 1. 创建优势产品类别表
CREATE TABLE IF NOT EXISTS advantage_product_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) NOT NULL UNIQUE,           -- 类别编码（如 HOME_APPLIANCE）
    name VARCHAR(100) NOT NULL,                 -- 类别名称（如 白色家电）
    description TEXT,                           -- 类别描述
    sort_order INTEGER DEFAULT 0,               -- 排序序号
    is_active INTEGER DEFAULT 1,                -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. 创建优势产品表
CREATE TABLE IF NOT EXISTS advantage_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_code VARCHAR(50) NOT NULL UNIQUE,   -- 产品编码（如 KC2701）
    product_name VARCHAR(200) NOT NULL,         -- 产品名称（如 离线双工位FCT）
    category_id INTEGER,                        -- 所属类别ID
    series_code VARCHAR(50),                    -- 产品系列编码（如 KC2700）
    description TEXT,                           -- 产品描述
    is_active INTEGER DEFAULT 1,                -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES advantage_product_categories(id)
);

-- 3. 创建索引
CREATE INDEX IF NOT EXISTS idx_advantage_products_category ON advantage_products(category_id);
CREATE INDEX IF NOT EXISTS idx_advantage_products_code ON advantage_products(product_code);
CREATE INDEX IF NOT EXISTS idx_advantage_products_series ON advantage_products(series_code);
CREATE INDEX IF NOT EXISTS idx_advantage_product_categories_code ON advantage_product_categories(code);

-- 4. 插入默认类别数据
INSERT OR IGNORE INTO advantage_product_categories (code, name, sort_order, is_active) VALUES
    ('HOME_APPLIANCE', '白色家电', 1, 1),
    ('AUTOMOTIVE', '汽车电子', 2, 1),
    ('NEW_ENERGY', '新能源', 3, 1),
    ('SEMICONDUCTOR', '半导体', 4, 1),
    ('POWER_TOOLS', '电动工具', 5, 1),
    ('AUTOMATION_LINE', '自动化线体', 6, 1),
    ('OTHER_EQUIPMENT', '其他设备', 7, 1),
    ('EDUCATION', '教育实训', 8, 1);

-- 5. 为 projects 表添加产品相关字段（如果不存在）
-- 注意：SQLite 不支持 ALTER TABLE ADD COLUMN IF NOT EXISTS，需要检查

-- 检查并添加 product_id 字段
-- SQLite 需要手动检查列是否存在，这里假设列不存在
-- 实际执行时如果列已存在会报错，可以忽略

-- ALTER TABLE projects ADD COLUMN product_id INTEGER REFERENCES advantage_products(id);
-- ALTER TABLE projects ADD COLUMN product_name VARCHAR(200);
-- ALTER TABLE projects ADD COLUMN product_match_type VARCHAR(20) DEFAULT 'UNKNOWN';
