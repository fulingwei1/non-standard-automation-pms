-- ============================================
-- 采购物料成本清单模块 - MySQL 迁移文件
-- 创建日期: 2025-01-15
-- 说明: 添加采购物料成本清单表（采购部维护的标准件成本信息）
-- ============================================

-- 采购物料成本清单表
CREATE TABLE IF NOT EXISTS purchase_material_costs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    material_code VARCHAR(50) COMMENT '物料编码',
    material_name VARCHAR(200) NOT NULL COMMENT '物料名称',
    specification VARCHAR(500) COMMENT '规格型号',
    brand VARCHAR(100) COMMENT '品牌',
    unit VARCHAR(20) DEFAULT '件' COMMENT '单位',
    material_type VARCHAR(50) COMMENT '物料类型：标准件/电气件/机械件等',
    is_standard_part BOOLEAN DEFAULT TRUE COMMENT '是否标准件',
    unit_cost DECIMAL(12, 4) NOT NULL COMMENT '单位成本',
    currency VARCHAR(10) DEFAULT 'CNY' COMMENT '币种',
    supplier_id INT COMMENT '供应商ID',
    supplier_name VARCHAR(200) COMMENT '供应商名称',
    purchase_date DATE COMMENT '采购日期',
    purchase_order_no VARCHAR(50) COMMENT '采购订单号',
    purchase_quantity DECIMAL(10, 4) COMMENT '采购数量',
    lead_time_days INT COMMENT '交期(天)',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用（用于自动匹配）',
    match_priority INT DEFAULT 0 COMMENT '匹配优先级（数字越大优先级越高）',
    match_keywords TEXT COMMENT '匹配关键词（逗号分隔，用于模糊匹配）',
    usage_count INT DEFAULT 0 COMMENT '使用次数（被匹配次数）',
    last_used_at DATETIME COMMENT '最后使用时间',
    remark TEXT COMMENT '备注',
    submitted_by INT COMMENT '提交人ID（采购部）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (submitted_by) REFERENCES users(id),
    INDEX idx_material_code (material_code),
    INDEX idx_material_name (material_name),
    INDEX idx_material_type (material_type),
    INDEX idx_is_standard (is_standard_part),
    INDEX idx_is_active (is_active),
    INDEX idx_match_priority (match_priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='采购物料成本清单表';
