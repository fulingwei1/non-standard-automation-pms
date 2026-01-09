-- =====================================================
-- BOM管理模块 - 数据库DDL脚本
-- 创建时间: 2026-01-03
-- 数据库: MySQL 8.0+
-- =====================================================

-- -----------------------------------------------------
-- 1. 物料主数据表
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `material` (
    `material_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '物料ID',
    `material_code` VARCHAR(30) NOT NULL COMMENT '物料编码',
    `material_name` VARCHAR(200) NOT NULL COMMENT '物料名称',
    `specification` VARCHAR(200) NULL COMMENT '规格型号',
    `brand` VARCHAR(50) NULL COMMENT '品牌',
    `category` VARCHAR(20) NOT NULL COMMENT '大类：ME/EL/PN/ST/OT/TR',
    `sub_category` VARCHAR(50) NULL COMMENT '子类别',
    `unit` VARCHAR(20) DEFAULT 'pcs' COMMENT '单位',
    `reference_price` DECIMAL(12,2) NULL COMMENT '参考单价',
    `default_supplier_id` BIGINT NULL COMMENT '默认供应商ID',
    `default_supplier_name` VARCHAR(100) NULL COMMENT '默认供应商',
    `lead_time` INT DEFAULT 7 COMMENT '标准采购周期(天)',
    `min_order_qty` DECIMAL(10,2) DEFAULT 1 COMMENT '最小起订量',
    `is_standard` TINYINT DEFAULT 0 COMMENT '是否标准件：0否1是',
    `status` VARCHAR(20) DEFAULT '启用' COMMENT '状态：启用/停用',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `created_by` BIGINT NOT NULL COMMENT '创建人ID',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除：0否1是',
    PRIMARY KEY (`material_id`),
    UNIQUE KEY `uk_material_code` (`material_code`),
    KEY `idx_material_category` (`category`),
    KEY `idx_material_name` (`material_name`),
    KEY `idx_material_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='物料主数据表';

-- -----------------------------------------------------
-- 2. BOM头表
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `bom_header` (
    `bom_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'BOM ID',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `project_code` VARCHAR(30) NOT NULL COMMENT '项目编号',
    `machine_no` VARCHAR(30) NOT NULL COMMENT '机台号',
    `machine_name` VARCHAR(100) NULL COMMENT '机台名称',
    `bom_type` VARCHAR(20) DEFAULT '整机' COMMENT 'BOM类型：整机/模块/备件',
    `current_version` VARCHAR(10) DEFAULT 'V1.0' COMMENT '当前版本',
    `status` VARCHAR(20) DEFAULT '草稿' COMMENT '状态：草稿/评审中/已发布/已冻结',
    `total_items` INT DEFAULT 0 COMMENT '物料总数',
    `total_cost` DECIMAL(14,2) DEFAULT 0 COMMENT '预估总成本',
    `kit_rate` DECIMAL(5,2) DEFAULT 0 COMMENT '齐套率%',
    `designer_id` BIGINT NOT NULL COMMENT '设计人ID',
    `designer_name` VARCHAR(50) NOT NULL COMMENT '设计人',
    `reviewer_id` BIGINT NULL COMMENT '审核人ID',
    `reviewer_name` VARCHAR(50) NULL COMMENT '审核人',
    `review_time` DATETIME NULL COMMENT '审核时间',
    `publish_time` DATETIME NULL COMMENT '发布时间',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `created_by` BIGINT NOT NULL COMMENT '创建人ID',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除：0否1是',
    PRIMARY KEY (`bom_id`),
    KEY `idx_bom_project` (`project_id`),
    KEY `idx_bom_machine` (`machine_no`),
    KEY `idx_bom_status` (`status`),
    KEY `idx_bom_designer` (`designer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='BOM头表';

-- -----------------------------------------------------
-- 3. BOM明细表
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `bom_item` (
    `item_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '明细ID',
    `bom_id` BIGINT NOT NULL COMMENT 'BOM ID',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `line_no` INT NOT NULL COMMENT '行号',
    `material_id` BIGINT NULL COMMENT '物料ID',
    `material_code` VARCHAR(30) NOT NULL COMMENT '物料编码',
    `material_name` VARCHAR(200) NOT NULL COMMENT '物料名称',
    `specification` VARCHAR(200) NULL COMMENT '规格型号',
    `brand` VARCHAR(50) NULL COMMENT '品牌',
    `category` VARCHAR(30) NOT NULL COMMENT '物料类别',
    `category_name` VARCHAR(50) NULL COMMENT '类别名称',
    `unit` VARCHAR(20) DEFAULT 'pcs' COMMENT '单位',
    `quantity` DECIMAL(10,2) NOT NULL COMMENT '需求数量',
    `unit_price` DECIMAL(12,2) NULL COMMENT '单价',
    `amount` DECIMAL(12,2) NULL COMMENT '金额',
    `supplier_id` BIGINT NULL COMMENT '供应商ID',
    `supplier_name` VARCHAR(100) NULL COMMENT '供应商名称',
    `lead_time` INT NULL COMMENT '采购周期(天)',
    `is_long_lead` TINYINT DEFAULT 0 COMMENT '是否长周期：0否1是',
    `is_key_part` TINYINT DEFAULT 0 COMMENT '是否关键件：0否1是',
    `required_date` DATE NULL COMMENT '需求日期',
    `ordered_qty` DECIMAL(10,2) DEFAULT 0 COMMENT '已下单数量',
    `received_qty` DECIMAL(10,2) DEFAULT 0 COMMENT '已到货数量',
    `stock_qty` DECIMAL(10,2) DEFAULT 0 COMMENT '库存可用',
    `shortage_qty` DECIMAL(10,2) DEFAULT 0 COMMENT '缺料数量',
    `procurement_status` VARCHAR(20) DEFAULT '待采购' COMMENT '采购状态',
    `drawing_no` VARCHAR(50) NULL COMMENT '图纸号',
    `position_no` VARCHAR(50) NULL COMMENT '位置号',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `version` VARCHAR(10) DEFAULT 'V1.0' COMMENT '版本',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除：0否1是',
    PRIMARY KEY (`item_id`),
    KEY `idx_item_bom` (`bom_id`),
    KEY `idx_item_project` (`project_id`),
    KEY `idx_item_material` (`material_id`),
    KEY `idx_item_category` (`category`),
    KEY `idx_item_status` (`procurement_status`),
    CONSTRAINT `fk_item_bom` FOREIGN KEY (`bom_id`)
        REFERENCES `bom_header` (`bom_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='BOM明细表';

-- -----------------------------------------------------
-- 4. BOM版本表
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `bom_version` (
    `version_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '版本ID',
    `bom_id` BIGINT NOT NULL COMMENT 'BOM ID',
    `version` VARCHAR(10) NOT NULL COMMENT '版本号',
    `version_type` VARCHAR(20) NOT NULL COMMENT '版本类型：初始/变更/修订',
    `ecn_id` BIGINT NULL COMMENT '关联ECN ID',
    `ecn_code` VARCHAR(30) NULL COMMENT 'ECN编号',
    `change_summary` VARCHAR(500) NULL COMMENT '变更摘要',
    `total_items` INT DEFAULT 0 COMMENT '物料总数',
    `total_cost` DECIMAL(14,2) DEFAULT 0 COMMENT '版本成本',
    `snapshot_data` LONGTEXT NULL COMMENT 'BOM快照JSON',
    `published_by` BIGINT NOT NULL COMMENT '发布人ID',
    `published_name` VARCHAR(50) NOT NULL COMMENT '发布人',
    `published_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '发布时间',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    PRIMARY KEY (`version_id`),
    KEY `idx_version_bom` (`bom_id`),
    KEY `idx_version_ecn` (`ecn_id`),
    CONSTRAINT `fk_version_bom` FOREIGN KEY (`bom_id`)
        REFERENCES `bom_header` (`bom_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='BOM版本表';

-- -----------------------------------------------------
-- 5. 物料类别字典表（可选）
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `material_category` (
    `category_id` INT NOT NULL AUTO_INCREMENT COMMENT '类别ID',
    `category_code` VARCHAR(10) NOT NULL COMMENT '类别编码',
    `category_name` VARCHAR(50) NOT NULL COMMENT '类别名称',
    `parent_code` VARCHAR(10) NULL COMMENT '父类别编码',
    `sort_order` INT DEFAULT 0 COMMENT '排序',
    `is_active` TINYINT DEFAULT 1 COMMENT '是否启用',
    PRIMARY KEY (`category_id`),
    UNIQUE KEY `uk_category_code` (`category_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='物料类别字典表';

-- 初始化物料类别数据
INSERT INTO `material_category` (`category_code`, `category_name`, `sort_order`) VALUES
('ME', '机械件', 1),
('EL', '电气件', 2),
('PN', '气动件', 3),
('ST', '标准件', 4),
('OT', '外协件', 5),
('TR', '贸易件', 6);

-- -----------------------------------------------------
-- 6. 供应商表（关联表）
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `supplier` (
    `supplier_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '供应商ID',
    `supplier_code` VARCHAR(30) NOT NULL COMMENT '供应商编码',
    `supplier_name` VARCHAR(100) NOT NULL COMMENT '供应商名称',
    `short_name` VARCHAR(50) NULL COMMENT '简称',
    `contact_person` VARCHAR(50) NULL COMMENT '联系人',
    `contact_phone` VARCHAR(20) NULL COMMENT '联系电话',
    `contact_email` VARCHAR(100) NULL COMMENT '邮箱',
    `address` VARCHAR(300) NULL COMMENT '地址',
    `category` VARCHAR(50) NULL COMMENT '供应商类别',
    `rating` VARCHAR(10) NULL COMMENT '评级：A/B/C/D',
    `payment_terms` VARCHAR(100) NULL COMMENT '付款条件',
    `lead_time` INT DEFAULT 7 COMMENT '标准交货周期(天)',
    `status` VARCHAR(20) DEFAULT '合作中' COMMENT '状态',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `created_by` BIGINT NOT NULL COMMENT '创建人ID',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除',
    PRIMARY KEY (`supplier_id`),
    UNIQUE KEY `uk_supplier_code` (`supplier_code`),
    KEY `idx_supplier_name` (`supplier_name`),
    KEY `idx_supplier_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='供应商表';

-- -----------------------------------------------------
-- 7. 物料-供应商关联表
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `material_supplier` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `material_id` BIGINT NOT NULL COMMENT '物料ID',
    `supplier_id` BIGINT NOT NULL COMMENT '供应商ID',
    `is_primary` TINYINT DEFAULT 0 COMMENT '是否主供应商',
    `unit_price` DECIMAL(12,2) NULL COMMENT '采购单价',
    `min_order_qty` DECIMAL(10,2) DEFAULT 1 COMMENT '最小起订量',
    `lead_time` INT DEFAULT 7 COMMENT '采购周期(天)',
    `remark` VARCHAR(200) NULL COMMENT '备注',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_material_supplier` (`material_id`, `supplier_id`),
    KEY `idx_ms_material` (`material_id`),
    KEY `idx_ms_supplier` (`supplier_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='物料-供应商关联表';

-- -----------------------------------------------------
-- 8. 创建视图：缺料汇总视图
-- -----------------------------------------------------
CREATE OR REPLACE VIEW `v_shortage_summary` AS
SELECT
    bi.item_id,
    bi.bom_id,
    bh.project_id,
    bh.project_code,
    bh.machine_no,
    bh.machine_name,
    bi.material_code,
    bi.material_name,
    bi.specification,
    bi.category,
    bi.category_name,
    bi.unit,
    bi.quantity,
    bi.ordered_qty,
    bi.received_qty,
    bi.stock_qty,
    bi.shortage_qty,
    bi.required_date,
    bi.lead_time,
    bi.supplier_name,
    bi.procurement_status,
    bi.is_key_part,
    bi.is_long_lead
FROM bom_item bi
JOIN bom_header bh ON bi.bom_id = bh.bom_id
WHERE bi.is_deleted = 0
  AND bh.is_deleted = 0
  AND bi.shortage_qty > 0
  AND bh.status IN ('已发布', '评审中');

-- -----------------------------------------------------
-- 9. 创建视图：BOM统计视图
-- -----------------------------------------------------
CREATE OR REPLACE VIEW `v_bom_statistics` AS
SELECT
    bh.bom_id,
    bh.project_id,
    bh.project_code,
    bh.machine_no,
    bh.machine_name,
    bh.status,
    bh.current_version,
    bh.designer_name,
    bh.total_items,
    bh.total_cost,
    bh.kit_rate,
    COUNT(CASE WHEN bi.category = 'ME' THEN 1 END) AS me_count,
    COUNT(CASE WHEN bi.category = 'EL' THEN 1 END) AS el_count,
    COUNT(CASE WHEN bi.category = 'PN' THEN 1 END) AS pn_count,
    COUNT(CASE WHEN bi.category = 'ST' THEN 1 END) AS st_count,
    COUNT(CASE WHEN bi.category = 'OT' THEN 1 END) AS ot_count,
    COUNT(CASE WHEN bi.category = 'TR' THEN 1 END) AS tr_count,
    SUM(CASE WHEN bi.shortage_qty > 0 THEN 1 ELSE 0 END) AS shortage_count,
    SUM(CASE WHEN bi.is_key_part = 1 THEN 1 ELSE 0 END) AS key_part_count,
    SUM(CASE WHEN bi.is_long_lead = 1 THEN 1 ELSE 0 END) AS long_lead_count
FROM bom_header bh
LEFT JOIN bom_item bi ON bh.bom_id = bi.bom_id AND bi.is_deleted = 0
WHERE bh.is_deleted = 0
GROUP BY bh.bom_id;

-- =====================================================
-- 索引优化建议（根据实际查询模式添加）
-- =====================================================
-- 复合索引示例（如需要）：
-- ALTER TABLE bom_item ADD INDEX idx_item_shortage (bom_id, shortage_qty, is_deleted);
-- ALTER TABLE bom_item ADD INDEX idx_item_procurement (project_id, procurement_status, is_deleted);
