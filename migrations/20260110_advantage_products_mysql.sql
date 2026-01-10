-- 优势产品管理迁移脚本 (MySQL)
-- 日期: 2026-01-10
-- 描述: 创建优势产品类别和优势产品表，用于管理公司主推产品

-- 1. 创建优势产品类别表
CREATE TABLE IF NOT EXISTS advantage_product_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE COMMENT '类别编码（如 HOME_APPLIANCE）',
    name VARCHAR(100) NOT NULL COMMENT '类别名称（如 白色家电）',
    description TEXT COMMENT '类别描述',
    sort_order INT DEFAULT 0 COMMENT '排序序号',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='优势产品类别';

-- 2. 创建优势产品表
CREATE TABLE IF NOT EXISTS advantage_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_code VARCHAR(50) NOT NULL UNIQUE COMMENT '产品编码（如 KC2701）',
    product_name VARCHAR(200) NOT NULL COMMENT '产品名称（如 离线双工位FCT）',
    category_id INT COMMENT '所属类别ID',
    series_code VARCHAR(50) COMMENT '产品系列编码（如 KC2700）',
    description TEXT COMMENT '产品描述',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_advantage_products_category FOREIGN KEY (category_id) REFERENCES advantage_product_categories(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='优势产品';

-- 3. 创建索引
CREATE INDEX idx_advantage_products_category ON advantage_products(category_id);
CREATE INDEX idx_advantage_products_code ON advantage_products(product_code);
CREATE INDEX idx_advantage_products_series ON advantage_products(series_code);
CREATE INDEX idx_advantage_product_categories_code ON advantage_product_categories(code);

-- 4. 插入默认类别数据
INSERT IGNORE INTO advantage_product_categories (code, name, sort_order, is_active) VALUES
    ('HOME_APPLIANCE', '白色家电', 1, 1),
    ('AUTOMOTIVE', '汽车电子', 2, 1),
    ('NEW_ENERGY', '新能源', 3, 1),
    ('SEMICONDUCTOR', '半导体', 4, 1),
    ('POWER_TOOLS', '电动工具', 5, 1),
    ('AUTOMATION_LINE', '自动化线体', 6, 1),
    ('OTHER_EQUIPMENT', '其他设备', 7, 1),
    ('EDUCATION', '教育实训', 8, 1);

-- 5. 为 projects 表添加产品相关字段
ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS product_id INT COMMENT '关联优势产品ID',
    ADD COLUMN IF NOT EXISTS product_name_input VARCHAR(200) COMMENT '手动输入的产品名称',
    ADD COLUMN IF NOT EXISTS product_match_type VARCHAR(20) DEFAULT 'UNKNOWN' COMMENT '产品匹配类型: ADVANTAGE/NEW/UNKNOWN';

-- 6. 添加外键约束
ALTER TABLE projects
    ADD CONSTRAINT fk_projects_advantage_product FOREIGN KEY (product_id) REFERENCES advantage_products(id) ON DELETE SET NULL;

-- 7. 创建索引
CREATE INDEX idx_projects_product ON projects(product_id);
CREATE INDEX idx_projects_product_match_type ON projects(product_match_type);
