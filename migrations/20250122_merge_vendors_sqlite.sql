-- ============================================================================
-- 数据库迁移脚本: 合并 suppliers 和 outsourcing_vendors 为统一的 vendors 表
-- 版本: 20250122
-- 数据库: SQLite
-- ============================================================================

-- 步骤 1: 创建新的 vendors 表
CREATE TABLE IF NOT EXISTS vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_code VARCHAR(50) UNIQUE NOT NULL,
    supplier_name VARCHAR(200) NOT NULL,
    supplier_short_name VARCHAR(50),
    supplier_type VARCHAR(20) NOT NULL,  -- 'MATERIAL' or 'OUTSOURCING'
    vendor_type VARCHAR(20) NOT NULL,    -- 同上，用于区分供应商类型

    -- 联系信息
    contact_person VARCHAR(50),
    contact_phone VARCHAR(30),
    contact_email VARCHAR(100),
    address VARCHAR(500),

    -- 资质信息
    business_license VARCHAR(100),
    qualification TEXT,
    capabilities TEXT,  -- JSON for outsourcing vendors

    -- 评价
    quality_rating DECIMAL(3,2) DEFAULT 0,
    delivery_rating DECIMAL(3,2) DEFAULT 0,
    service_rating DECIMAL(3,2) DEFAULT 0,
    overall_rating DECIMAL(3,2) DEFAULT 0,
    supplier_level VARCHAR(1) DEFAULT 'B',

    -- 财务信息
    bank_name VARCHAR(100),
    bank_account VARCHAR(50),
    tax_number VARCHAR(50),
    payment_terms VARCHAR(50),

    -- 状态
    status VARCHAR(20) DEFAULT 'ACTIVE',
    cooperation_start DATE,
    last_order_date DATE,

    remark TEXT,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_vendors_type ON vendors(vendor_type);
CREATE INDEX idx_vendors_status ON vendors(status);
CREATE INDEX idx_vendors_level ON vendors(supplier_level);

-- 步骤 2: 从 suppliers 表迁移数据到 vendors 表
INSERT INTO vendors (
    supplier_code,
    supplier_name,
    supplier_short_name,
    supplier_type,
    vendor_type,
    contact_person,
    contact_phone,
    contact_email,
    address,
    business_license,
    qualification,
    quality_rating,
    delivery_rating,
    service_rating,
    overall_rating,
    supplier_level,
    bank_name,
    bank_account,
    tax_number,
    payment_terms,
    status,
    cooperation_start,
    last_order_date,
    remark,
    created_by,
    created_at,
    updated_at
)
SELECT
    supplier_code,
    supplier_name,
    supplier_short_name,
    COALESCE(supplier_type, 'MATERIAL'),
    'MATERIAL',
    contact_person,
    contact_phone,
    contact_email,
    address,
    business_license,
    qualification,
    quality_rating,
    delivery_rating,
    service_rating,
    overall_rating,
    supplier_level,
    bank_name,
    bank_account,
    tax_number,
    payment_terms,
    status,
    cooperation_start,
    last_order_date,
    remark,
    created_by,
    created_at,
    updated_at
FROM suppliers;

-- 步骤 3: 从 outsourcing_vendors 表迁移数据到 vendors 表
INSERT INTO vendors (
    supplier_code,
    supplier_name,
    supplier_short_name,
    supplier_type,
    vendor_type,
    contact_person,
    contact_phone,
    contact_email,
    address,
    business_license,
    capabilities,
    quality_rating,
    delivery_rating,
    service_rating,
    overall_rating,
    bank_name,
    bank_account,
    tax_number,
    status,
    cooperation_start,
    last_order_date,
    remark,
    created_by,
    created_at,
    updated_at
)
SELECT
    vendor_code,
    vendor_name,
    vendor_short_name,
    'OUTSOURCING',
    'OUTSOURCING',
    contact_person,
    contact_phone,
    contact_email,
    address,
    business_license,
    json_extract(qualification, '$'),  -- 提取 JSON
    quality_rating,
    delivery_rating,
    service_rating,
    overall_rating,
    bank_name,
    bank_account,
    tax_number,
    status,
    cooperation_start,
    last_order_date,
    remark,
    created_by,
    created_at,
    updated_at
FROM outsourcing_vendors;

-- 步骤 4: 重命名旧表（备份）
ALTER TABLE suppliers RENAME TO suppliers_backup_20250122;
ALTER TABLE outsourcing_vendors RENAME TO outsourcing_vendors_backup_20250122;

-- 步骤 5: 更新外键引用
-- 更新 material_suppliers 表
UPDATE material_suppliers SET supplier_id = (
    SELECT id FROM vendors WHERE vendor_type = 'MATERIAL' AND suppliers_backup_20250122.id = supplier_id
)
WHERE supplier_id IN (SELECT id FROM suppliers_backup_20250122);

-- 更新 purchase_orders 表
UPDATE purchase_orders SET supplier_id = (
    SELECT id FROM vendors WHERE vendor_type = 'MATERIAL' AND suppliers_backup_20250122.id = supplier_id
)
WHERE supplier_id IN (SELECT id FROM suppliers_backup_20250122);

-- 更新 materials 表的 default_supplier_id
UPDATE materials SET default_supplier_id = (
    SELECT id FROM vendors WHERE vendor_type = 'MATERIAL' AND suppliers_backup_20250122.id = default_supplier_id
)
WHERE default_supplier_id IN (SELECT id FROM suppliers_backup_20250122);

-- 更新 outsourcing_orders 表
UPDATE outsourcing_orders SET vendor_id = (
    SELECT id FROM vendors WHERE vendor_type = 'OUTSOURCING' AND outsourcing_vendors_backup_20250122.id = vendor_id
)
WHERE vendor_id IN (SELECT id FROM outsourcing_vendors_backup_20250122);

-- 更新 outsourcing_deliveries 表
UPDATE outsourcing_deliveries SET vendor_id = (
    SELECT id FROM vendors WHERE vendor_type = 'OUTSOURCING' AND outsourcing_vendors_backup_20250122.id = vendor_id
)
WHERE vendor_id IN (SELECT id FROM outsourcing_vendors_backup_20250122);

-- 更新 outsourcing_payments 表
UPDATE outsourcing_payments SET vendor_id = (
    SELECT id FROM vendors WHERE vendor_type = 'OUTSOURCING' AND outsourcing_vendors_backup_20250122.id = vendor_id
)
WHERE vendor_id IN (SELECT id FROM outsourcing_vendors_backup_20250122);

-- 更新 outsourcing_evaluations 表
UPDATE outsourcing_evaluations SET vendor_id = (
    SELECT id FROM vendors WHERE vendor_type = 'OUTSOURCING' AND outsourcing_vendors_backup_20250122.id = vendor_id
)
WHERE vendor_id IN (SELECT id FROM outsourcing_vendors_backup_20250122);

-- 步骤 6: 创建视图以保持向后兼容（可选，用于过渡期）
CREATE VIEW suppliers_view AS
SELECT id, supplier_code, supplier_name, supplier_short_name,
       supplier_type, contact_person, contact_phone, contact_email,
       address, business_license, qualification, quality_rating,
       delivery_rating, service_rating, overall_rating, supplier_level,
       bank_name, bank_account, tax_number, payment_terms,
       status, cooperation_start, last_order_date, remark,
       created_by, created_at, updated_at
FROM vendors
WHERE vendor_type = 'MATERIAL';

CREATE VIEW outsourcing_vendors_view AS
SELECT id, supplier_code AS vendor_code, supplier_name AS vendor_name,
       supplier_short_name AS vendor_short_name, vendor_type,
       contact_person, contact_phone, contact_email, address,
       business_license, capabilities AS qualification,
       quality_rating, delivery_rating, service_rating, overall_rating,
       bank_name, bank_account, tax_number, status,
       cooperation_start, last_order_date, remark,
       created_by, created_at, updated_at
FROM vendors
WHERE vendor_type = 'OUTSOURCING';

-- ============================================================================
-- 回滚脚本（如果需要恢复）
-- ============================================================================
-- DROP VIEW suppliers_view;
-- DROP VIEW outsourcing_vendors_view;
-- DROP TABLE vendors;
-- ALTER TABLE suppliers_backup_20250122 RENAME TO suppliers;
-- ALTER TABLE outsourcing_vendors_backup_20250122 RENAME TO outsourcing_vendors;
-- -- 注意：需要手动恢复外键引用
