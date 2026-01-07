-- ============================================
-- 采购与物料管理模块 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2025-07-12
-- 说明: 物料、供应商、BOM、采购单、收货等表
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. 物料主数据表
-- ============================================

CREATE TABLE IF NOT EXISTS `materials` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `material_code`       VARCHAR(50) NOT NULL COMMENT '物料编码',
    `material_name`       VARCHAR(200) NOT NULL COMMENT '物料名称',
    `specification`       VARCHAR(500) DEFAULT NULL COMMENT '规格型号',

    -- 分类
    `category_l1`         VARCHAR(50) DEFAULT NULL COMMENT '一级分类',
    `category_l2`         VARCHAR(50) DEFAULT NULL COMMENT '二级分类',
    `category_l3`         VARCHAR(50) DEFAULT NULL COMMENT '三级分类',
    `material_type`       VARCHAR(20) DEFAULT 'PURCHASE' COMMENT '物料类型',

    -- 基本属性
    `unit`                VARCHAR(20) DEFAULT '件' COMMENT '基本单位',
    `brand`               VARCHAR(100) DEFAULT NULL COMMENT '品牌',
    `model`               VARCHAR(100) DEFAULT NULL COMMENT '型号',

    -- 采购属性
    `default_supplier_id` INT UNSIGNED DEFAULT NULL COMMENT '默认供应商',
    `lead_time_days`      INT DEFAULT 7 COMMENT '采购周期',
    `min_order_qty`       DECIMAL(10,2) DEFAULT 1 COMMENT '最小起订量',
    `price_unit`          DECIMAL(12,4) DEFAULT NULL COMMENT '参考单价',

    -- 库存属性
    `safety_stock`        DECIMAL(10,2) DEFAULT 0 COMMENT '安全库存',
    `reorder_point`       DECIMAL(10,2) DEFAULT 0 COMMENT '再订货点',

    -- 质量属性
    `inspection_required` TINYINT(1) DEFAULT 0 COMMENT '是否需要检验',
    `shelf_life_days`     INT DEFAULT NULL COMMENT '保质期',

    -- 图纸信息
    `drawing_no`          VARCHAR(100) DEFAULT NULL COMMENT '图号',
    `drawing_version`     VARCHAR(20) DEFAULT NULL COMMENT '图纸版本',
    `drawing_file`        VARCHAR(500) DEFAULT NULL COMMENT '图纸文件路径',

    -- 状态
    `status`              VARCHAR(20) DEFAULT 'ACTIVE' COMMENT '状态',

    -- 描述
    `description`         TEXT DEFAULT NULL,
    `remark`              TEXT DEFAULT NULL,

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_material_code` (`material_code`),
    KEY `idx_materials_name` (`material_name`),
    KEY `idx_materials_category` (`category_l1`, `category_l2`),
    KEY `idx_materials_type` (`material_type`),
    KEY `idx_materials_status` (`status`),
    CONSTRAINT `fk_materials_supplier` FOREIGN KEY (`default_supplier_id`) REFERENCES `suppliers` (`id`),
    CONSTRAINT `fk_materials_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='物料主数据表';

-- ============================================
-- 2. 供应商表
-- ============================================

CREATE TABLE IF NOT EXISTS `suppliers` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `supplier_code`       VARCHAR(50) NOT NULL COMMENT '供应商编码',
    `supplier_name`       VARCHAR(200) NOT NULL COMMENT '供应商名称',
    `short_name`          VARCHAR(50) DEFAULT NULL COMMENT '简称',

    -- 分类
    `supplier_type`       VARCHAR(20) DEFAULT 'MATERIAL' COMMENT '供应商类型',
    `category`            VARCHAR(50) DEFAULT NULL COMMENT '供应商分类',

    -- 联系信息
    `contact_person`      VARCHAR(50) DEFAULT NULL COMMENT '联系人',
    `contact_phone`       VARCHAR(50) DEFAULT NULL COMMENT '联系电话',
    `contact_email`       VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    `contact_fax`         VARCHAR(50) DEFAULT NULL COMMENT '传真',
    `address`             VARCHAR(500) DEFAULT NULL COMMENT '地址',

    -- 公司信息
    `legal_person`        VARCHAR(50) DEFAULT NULL COMMENT '法人',
    `tax_no`              VARCHAR(50) DEFAULT NULL COMMENT '税号',
    `bank_name`           VARCHAR(100) DEFAULT NULL COMMENT '开户银行',
    `bank_account`        VARCHAR(50) DEFAULT NULL COMMENT '银行账号',

    -- 合作信息
    `cooperation_status`  VARCHAR(20) DEFAULT 'ACTIVE' COMMENT '合作状态',
    `cooperation_level`   VARCHAR(20) DEFAULT 'NORMAL' COMMENT '合作级别',
    `contract_start`      DATE DEFAULT NULL COMMENT '合同开始',
    `contract_end`        DATE DEFAULT NULL COMMENT '合同结束',

    -- 付款信息
    `payment_terms`       VARCHAR(50) DEFAULT NULL COMMENT '付款条款',
    `payment_days`        INT DEFAULT 30 COMMENT '账期',
    `currency`            VARCHAR(10) DEFAULT 'CNY' COMMENT '币种',
    `tax_rate`            DECIMAL(5,2) DEFAULT 13 COMMENT '税率',

    -- 评价信息
    `quality_rating`      DECIMAL(3,2) DEFAULT 0 COMMENT '质量评分',
    `delivery_rating`     DECIMAL(3,2) DEFAULT 0 COMMENT '交期评分',
    `service_rating`      DECIMAL(3,2) DEFAULT 0 COMMENT '服务评分',
    `overall_rating`      DECIMAL(3,2) DEFAULT 0 COMMENT '综合评分',

    -- 资质信息
    `certifications`      JSON DEFAULT NULL COMMENT '资质证书',

    -- 备注
    `remark`              TEXT DEFAULT NULL,

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_supplier_code` (`supplier_code`),
    KEY `idx_suppliers_name` (`supplier_name`),
    KEY `idx_suppliers_type` (`supplier_type`),
    KEY `idx_suppliers_status` (`cooperation_status`),
    CONSTRAINT `fk_suppliers_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='供应商表';

-- ============================================
-- 3. 供应商物料报价表
-- ============================================

CREATE TABLE IF NOT EXISTS `supplier_quotations` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `supplier_id`         INT UNSIGNED NOT NULL COMMENT '供应商ID',
    `material_id`         INT UNSIGNED NOT NULL COMMENT '物料ID',

    `unit_price`          DECIMAL(12,4) NOT NULL COMMENT '单价',
    `currency`            VARCHAR(10) DEFAULT 'CNY' COMMENT '币种',
    `min_qty`             DECIMAL(10,2) DEFAULT 1 COMMENT '最小数量',
    `price_break_qty`     DECIMAL(10,2) DEFAULT NULL COMMENT '阶梯数量',
    `price_break_price`   DECIMAL(12,4) DEFAULT NULL COMMENT '阶梯价格',

    `lead_time_days`      INT DEFAULT NULL COMMENT '交期',

    `valid_from`          DATE DEFAULT NULL COMMENT '有效开始',
    `valid_to`            DATE DEFAULT NULL COMMENT '有效结束',

    `is_preferred`        TINYINT(1) DEFAULT 0 COMMENT '是否首选',
    `is_active`           TINYINT(1) DEFAULT 1 COMMENT '是否有效',

    `remark`              TEXT DEFAULT NULL,

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_quotations_supplier` (`supplier_id`),
    KEY `idx_quotations_material` (`material_id`),
    CONSTRAINT `fk_quotations_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`),
    CONSTRAINT `fk_quotations_material` FOREIGN KEY (`material_id`) REFERENCES `materials` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='供应商物料报价表';

-- ============================================
-- 4. BOM版本表
-- ============================================

CREATE TABLE IF NOT EXISTS `bom_versions` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `project_id`          INT UNSIGNED NOT NULL COMMENT '项目ID',
    `machine_id`          INT UNSIGNED DEFAULT NULL COMMENT '设备ID',

    `version_no`          VARCHAR(20) NOT NULL COMMENT '版本号',
    `version_name`        VARCHAR(100) DEFAULT NULL COMMENT '版本名称',

    `status`              VARCHAR(20) DEFAULT 'DRAFT' COMMENT '状态',
    `is_current`          TINYINT(1) DEFAULT 0 COMMENT '是否当前版本',

    `source_version_id`   INT UNSIGNED DEFAULT NULL COMMENT '来源版本',

    `total_items`         INT DEFAULT 0 COMMENT '物料总数',
    `total_amount`        DECIMAL(14,2) DEFAULT 0 COMMENT '预估总金额',

    `approved_by`         INT UNSIGNED DEFAULT NULL,
    `approved_at`         DATETIME DEFAULT NULL,

    `change_note`         TEXT DEFAULT NULL COMMENT '变更说明',

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_bom_versions_project` (`project_id`),
    KEY `idx_bom_versions_machine` (`machine_id`),
    KEY `idx_bom_versions_status` (`status`),
    CONSTRAINT `fk_bom_versions_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_bom_versions_machine` FOREIGN KEY (`machine_id`) REFERENCES `machines` (`id`),
    CONSTRAINT `fk_bom_versions_source` FOREIGN KEY (`source_version_id`) REFERENCES `bom_versions` (`id`),
    CONSTRAINT `fk_bom_versions_approved_by` FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_bom_versions_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='BOM版本表';

-- ============================================
-- 5. BOM明细表
-- ============================================

CREATE TABLE IF NOT EXISTS `bom_items` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `bom_version_id`      INT UNSIGNED NOT NULL COMMENT 'BOM版本ID',
    `material_id`         INT UNSIGNED DEFAULT NULL COMMENT '物料ID',

    `parent_item_id`      INT UNSIGNED DEFAULT NULL COMMENT '父级物料行ID',
    `level`               INT DEFAULT 1 COMMENT '层级',
    `item_no`             VARCHAR(20) DEFAULT NULL COMMENT '项号',

    `material_code`       VARCHAR(50) NOT NULL COMMENT '物料编码',
    `material_name`       VARCHAR(200) NOT NULL COMMENT '物料名称',
    `specification`       VARCHAR(500) DEFAULT NULL COMMENT '规格',
    `unit`                VARCHAR(20) DEFAULT '件' COMMENT '单位',

    `quantity`            DECIMAL(10,4) NOT NULL COMMENT '数量',
    `unit_price`          DECIMAL(12,4) DEFAULT NULL COMMENT '预估单价',
    `amount`              DECIMAL(14,2) DEFAULT NULL COMMENT '金额',

    `source_type`         VARCHAR(20) DEFAULT 'PURCHASE' COMMENT '来源类型',
    `supplier_id`         INT UNSIGNED DEFAULT NULL COMMENT '指定供应商',
    `lead_time_days`      INT DEFAULT NULL COMMENT '交期',

    `required_date`       DATE DEFAULT NULL COMMENT '需求日期',

    `drawing_no`          VARCHAR(100) DEFAULT NULL COMMENT '图号',
    `drawing_version`     VARCHAR(20) DEFAULT NULL COMMENT '图纸版本',

    `ordered_qty`         DECIMAL(10,4) DEFAULT 0 COMMENT '已订购数量',
    `received_qty`        DECIMAL(10,4) DEFAULT 0 COMMENT '已到货数量',
    `ready_status`        VARCHAR(20) DEFAULT 'NOT_READY' COMMENT '齐套状态',

    `remark`              TEXT DEFAULT NULL,

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_bom_items_version` (`bom_version_id`),
    KEY `idx_bom_items_material` (`material_id`),
    KEY `idx_bom_items_parent` (`parent_item_id`),
    KEY `idx_bom_items_ready` (`ready_status`),
    CONSTRAINT `fk_bom_items_version` FOREIGN KEY (`bom_version_id`) REFERENCES `bom_versions` (`id`),
    CONSTRAINT `fk_bom_items_material` FOREIGN KEY (`material_id`) REFERENCES `materials` (`id`),
    CONSTRAINT `fk_bom_items_parent` FOREIGN KEY (`parent_item_id`) REFERENCES `bom_items` (`id`),
    CONSTRAINT `fk_bom_items_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='BOM明细表';

-- ============================================
-- 6. 采购申请单表
-- ============================================

CREATE TABLE IF NOT EXISTS `purchase_requests` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `request_no`          VARCHAR(50) NOT NULL COMMENT '申请单号',
    `project_id`          INT UNSIGNED DEFAULT NULL COMMENT '项目ID',
    `machine_id`          INT UNSIGNED DEFAULT NULL COMMENT '设备ID',

    `request_type`        VARCHAR(20) DEFAULT 'NORMAL' COMMENT '申请类型',
    `request_reason`      TEXT DEFAULT NULL COMMENT '申请原因',
    `required_date`       DATE DEFAULT NULL COMMENT '需求日期',

    `total_amount`        DECIMAL(14,2) DEFAULT 0 COMMENT '总金额',

    `status`              VARCHAR(20) DEFAULT 'DRAFT' COMMENT '状态',

    `approved_by`         INT UNSIGNED DEFAULT NULL,
    `approved_at`         DATETIME DEFAULT NULL,
    `approval_note`       TEXT DEFAULT NULL,

    `requested_by`        INT UNSIGNED DEFAULT NULL,
    `requested_at`        DATETIME DEFAULT NULL,

    `remark`              TEXT DEFAULT NULL,

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_request_no` (`request_no`),
    KEY `idx_requests_project` (`project_id`),
    KEY `idx_requests_status` (`status`),
    CONSTRAINT `fk_requests_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_requests_machine` FOREIGN KEY (`machine_id`) REFERENCES `machines` (`id`),
    CONSTRAINT `fk_requests_approved_by` FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_requests_requested_by` FOREIGN KEY (`requested_by`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_requests_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='采购申请单表';

-- ============================================
-- 7. 采购申请明细表
-- ============================================

CREATE TABLE IF NOT EXISTS `purchase_request_items` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `request_id`          INT UNSIGNED NOT NULL COMMENT '申请单ID',
    `bom_item_id`         INT UNSIGNED DEFAULT NULL COMMENT 'BOM行ID',
    `material_id`         INT UNSIGNED DEFAULT NULL COMMENT '物料ID',

    `material_code`       VARCHAR(50) NOT NULL,
    `material_name`       VARCHAR(200) NOT NULL,
    `specification`       VARCHAR(500) DEFAULT NULL,
    `unit`                VARCHAR(20) DEFAULT '件',

    `quantity`            DECIMAL(10,4) NOT NULL COMMENT '申请数量',
    `unit_price`          DECIMAL(12,4) DEFAULT NULL COMMENT '预估单价',
    `amount`              DECIMAL(14,2) DEFAULT NULL COMMENT '金额',

    `required_date`       DATE DEFAULT NULL,

    `ordered_qty`         DECIMAL(10,4) DEFAULT 0 COMMENT '已采购数量',

    `remark`              TEXT DEFAULT NULL,

    PRIMARY KEY (`id`),
    KEY `idx_pr_items_request` (`request_id`),
    CONSTRAINT `fk_pr_items_request` FOREIGN KEY (`request_id`) REFERENCES `purchase_requests` (`id`),
    CONSTRAINT `fk_pr_items_bom` FOREIGN KEY (`bom_item_id`) REFERENCES `bom_items` (`id`),
    CONSTRAINT `fk_pr_items_material` FOREIGN KEY (`material_id`) REFERENCES `materials` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='采购申请明细表';

-- ============================================
-- 8. 采购订单表
-- ============================================

CREATE TABLE IF NOT EXISTS `purchase_orders` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `order_no`            VARCHAR(50) NOT NULL COMMENT '订单号',
    `project_id`          INT UNSIGNED DEFAULT NULL COMMENT '项目ID',
    `supplier_id`         INT UNSIGNED NOT NULL COMMENT '供应商ID',

    `order_type`          VARCHAR(20) DEFAULT 'NORMAL' COMMENT '订单类型',
    `order_date`          DATE NOT NULL COMMENT '订单日期',

    `required_date`       DATE DEFAULT NULL COMMENT '要求交期',
    `confirmed_date`      DATE DEFAULT NULL COMMENT '确认交期',

    `total_quantity`      DECIMAL(12,2) DEFAULT 0 COMMENT '总数量',
    `subtotal`            DECIMAL(14,2) DEFAULT 0 COMMENT '小计',
    `tax_rate`            DECIMAL(5,2) DEFAULT 13 COMMENT '税率',
    `tax_amount`          DECIMAL(12,2) DEFAULT 0 COMMENT '税额',
    `total_amount`        DECIMAL(14,2) DEFAULT 0 COMMENT '价税合计',

    `payment_terms`       VARCHAR(50) DEFAULT NULL COMMENT '付款条款',
    `currency`            VARCHAR(10) DEFAULT 'CNY' COMMENT '币种',

    `delivery_address`    VARCHAR(500) DEFAULT NULL COMMENT '收货地址',
    `receiver`            VARCHAR(50) DEFAULT NULL COMMENT '收货人',
    `receiver_phone`      VARCHAR(50) DEFAULT NULL COMMENT '联系电话',

    `status`              VARCHAR(20) DEFAULT 'DRAFT' COMMENT '状态',

    `approved_by`         INT UNSIGNED DEFAULT NULL,
    `approved_at`         DATETIME DEFAULT NULL,

    `received_amount`     DECIMAL(14,2) DEFAULT 0 COMMENT '已收货金额',

    `remark`              TEXT DEFAULT NULL,
    `internal_note`       TEXT DEFAULT NULL COMMENT '内部备注',

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_order_no` (`order_no`),
    KEY `idx_orders_project` (`project_id`),
    KEY `idx_orders_supplier` (`supplier_id`),
    KEY `idx_orders_status` (`status`),
    KEY `idx_orders_date` (`order_date`),
    CONSTRAINT `fk_orders_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_orders_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`),
    CONSTRAINT `fk_orders_approved_by` FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_orders_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='采购订单表';

-- ============================================
-- 9. 采购订单明细表
-- ============================================

CREATE TABLE IF NOT EXISTS `purchase_order_items` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `order_id`            INT UNSIGNED NOT NULL COMMENT '订单ID',
    `pr_item_id`          INT UNSIGNED DEFAULT NULL COMMENT '采购申请行ID',
    `bom_item_id`         INT UNSIGNED DEFAULT NULL COMMENT 'BOM行ID',
    `material_id`         INT UNSIGNED DEFAULT NULL COMMENT '物料ID',

    `item_no`             INT NOT NULL COMMENT '行号',

    `material_code`       VARCHAR(50) NOT NULL,
    `material_name`       VARCHAR(200) NOT NULL,
    `specification`       VARCHAR(500) DEFAULT NULL,
    `unit`                VARCHAR(20) DEFAULT '件',

    `quantity`            DECIMAL(10,4) NOT NULL COMMENT '数量',
    `unit_price`          DECIMAL(12,4) NOT NULL COMMENT '单价',
    `amount`              DECIMAL(14,2) NOT NULL COMMENT '金额',

    `required_date`       DATE DEFAULT NULL COMMENT '要求交期',

    `received_qty`        DECIMAL(10,4) DEFAULT 0 COMMENT '已收数量',
    `qualified_qty`       DECIMAL(10,4) DEFAULT 0 COMMENT '合格数量',
    `rejected_qty`        DECIMAL(10,4) DEFAULT 0 COMMENT '不合格数量',

    `status`              VARCHAR(20) DEFAULT 'PENDING' COMMENT '状态',

    `remark`              TEXT DEFAULT NULL,

    PRIMARY KEY (`id`),
    KEY `idx_po_items_order` (`order_id`),
    KEY `idx_po_items_material` (`material_id`),
    CONSTRAINT `fk_po_items_order` FOREIGN KEY (`order_id`) REFERENCES `purchase_orders` (`id`),
    CONSTRAINT `fk_po_items_pr` FOREIGN KEY (`pr_item_id`) REFERENCES `purchase_request_items` (`id`),
    CONSTRAINT `fk_po_items_bom` FOREIGN KEY (`bom_item_id`) REFERENCES `bom_items` (`id`),
    CONSTRAINT `fk_po_items_material` FOREIGN KEY (`material_id`) REFERENCES `materials` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='采购订单明细表';

-- ============================================
-- 10. 收货单表
-- ============================================

CREATE TABLE IF NOT EXISTS `goods_receipts` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `receipt_no`          VARCHAR(50) NOT NULL COMMENT '收货单号',
    `order_id`            INT UNSIGNED NOT NULL COMMENT '采购订单ID',
    `supplier_id`         INT UNSIGNED NOT NULL COMMENT '供应商ID',

    `receipt_date`        DATE NOT NULL COMMENT '收货日期',
    `receipt_type`        VARCHAR(20) DEFAULT 'NORMAL' COMMENT '收货类型',

    `tracking_no`         VARCHAR(100) DEFAULT NULL COMMENT '物流单号',
    `carrier`             VARCHAR(100) DEFAULT NULL COMMENT '承运商',

    `total_quantity`      DECIMAL(12,2) DEFAULT 0,

    `inspection_status`   VARCHAR(20) DEFAULT 'PENDING' COMMENT '检验状态',

    `warehouse_in_status` VARCHAR(20) DEFAULT 'PENDING' COMMENT '入库状态',

    `received_by`         INT UNSIGNED DEFAULT NULL COMMENT '收货人',

    `remark`              TEXT DEFAULT NULL,

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_receipt_no` (`receipt_no`),
    KEY `idx_receipts_order` (`order_id`),
    KEY `idx_receipts_date` (`receipt_date`),
    CONSTRAINT `fk_receipts_order` FOREIGN KEY (`order_id`) REFERENCES `purchase_orders` (`id`),
    CONSTRAINT `fk_receipts_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`),
    CONSTRAINT `fk_receipts_received_by` FOREIGN KEY (`received_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='收货单表';

-- ============================================
-- 11. 收货明细表
-- ============================================

CREATE TABLE IF NOT EXISTS `goods_receipt_items` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `receipt_id`          INT UNSIGNED NOT NULL COMMENT '收货单ID',
    `po_item_id`          INT UNSIGNED NOT NULL COMMENT '采购订单行ID',
    `material_id`         INT UNSIGNED DEFAULT NULL COMMENT '物料ID',

    `material_code`       VARCHAR(50) NOT NULL,
    `material_name`       VARCHAR(200) NOT NULL,

    `received_qty`        DECIMAL(10,4) NOT NULL COMMENT '收货数量',
    `qualified_qty`       DECIMAL(10,4) DEFAULT 0 COMMENT '合格数量',
    `rejected_qty`        DECIMAL(10,4) DEFAULT 0 COMMENT '不合格数量',

    `batch_no`            VARCHAR(50) DEFAULT NULL COMMENT '批次号',

    `inspection_result`   VARCHAR(20) DEFAULT NULL COMMENT '检验结果',
    `inspection_note`     TEXT DEFAULT NULL COMMENT '检验备注',

    `warehouse_in_qty`    DECIMAL(10,4) DEFAULT 0 COMMENT '入库数量',

    `remark`              TEXT DEFAULT NULL,

    PRIMARY KEY (`id`),
    KEY `idx_gr_items_receipt` (`receipt_id`),
    CONSTRAINT `fk_gr_items_receipt` FOREIGN KEY (`receipt_id`) REFERENCES `goods_receipts` (`id`),
    CONSTRAINT `fk_gr_items_po` FOREIGN KEY (`po_item_id`) REFERENCES `purchase_order_items` (`id`),
    CONSTRAINT `fk_gr_items_material` FOREIGN KEY (`material_id`) REFERENCES `materials` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='收货明细表';

-- ============================================
-- 12. 物料短缺预警表
-- ============================================

CREATE TABLE IF NOT EXISTS `shortage_alerts` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `project_id`          INT UNSIGNED NOT NULL COMMENT '项目ID',
    `machine_id`          INT UNSIGNED DEFAULT NULL COMMENT '设备ID',
    `bom_item_id`         INT UNSIGNED DEFAULT NULL COMMENT 'BOM行ID',
    `material_id`         INT UNSIGNED DEFAULT NULL COMMENT '物料ID',

    `material_code`       VARCHAR(50) NOT NULL,
    `material_name`       VARCHAR(200) NOT NULL,

    `required_qty`        DECIMAL(10,4) NOT NULL COMMENT '需求数量',
    `required_date`       DATE DEFAULT NULL COMMENT '需求日期',

    `ordered_qty`         DECIMAL(10,4) DEFAULT 0 COMMENT '已订购',
    `received_qty`        DECIMAL(10,4) DEFAULT 0 COMMENT '已到货',
    `shortage_qty`        DECIMAL(10,4) NOT NULL COMMENT '短缺数量',

    `alert_level`         VARCHAR(20) DEFAULT 'WARNING' COMMENT '预警级别',

    `status`              VARCHAR(20) DEFAULT 'OPEN' COMMENT '处理状态',

    `handled_by`          INT UNSIGNED DEFAULT NULL,
    `handled_at`          DATETIME DEFAULT NULL,
    `handle_note`         TEXT DEFAULT NULL,

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_shortage_project` (`project_id`),
    KEY `idx_shortage_status` (`status`),
    KEY `idx_shortage_level` (`alert_level`),
    CONSTRAINT `fk_shortage_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_shortage_machine` FOREIGN KEY (`machine_id`) REFERENCES `machines` (`id`),
    CONSTRAINT `fk_shortage_bom` FOREIGN KEY (`bom_item_id`) REFERENCES `bom_items` (`id`),
    CONSTRAINT `fk_shortage_material` FOREIGN KEY (`material_id`) REFERENCES `materials` (`id`),
    CONSTRAINT `fk_shortage_handled_by` FOREIGN KEY (`handled_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='物料短缺预警表';

-- ============================================
-- 13. 物料分类表
-- ============================================

CREATE TABLE IF NOT EXISTS `material_categories` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `category_code`       VARCHAR(50) NOT NULL COMMENT '分类编码',
    `category_name`       VARCHAR(100) NOT NULL COMMENT '分类名称',
    `parent_id`           INT UNSIGNED DEFAULT NULL COMMENT '父分类ID',
    `level`               INT DEFAULT 1 COMMENT '层级',
    `sort_order`          INT DEFAULT 0 COMMENT '排序',

    `description`         TEXT DEFAULT NULL,
    `is_active`           TINYINT(1) DEFAULT 1,

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_category_code` (`category_code`),
    KEY `idx_categories_parent` (`parent_id`),
    CONSTRAINT `fk_categories_parent` FOREIGN KEY (`parent_id`) REFERENCES `material_categories` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='物料分类表';

-- ============================================
-- 14. 视图定义
-- ============================================

-- BOM齐套率视图
CREATE OR REPLACE VIEW `v_bom_ready_rate` AS
SELECT
    bv.id as bom_version_id,
    bv.project_id,
    bv.machine_id,
    bv.version_no,
    COUNT(bi.id) as total_items,
    SUM(CASE WHEN bi.ready_status = 'READY' THEN 1 ELSE 0 END) as ready_items,
    ROUND(SUM(CASE WHEN bi.ready_status = 'READY' THEN 1 ELSE 0 END) * 100.0 / COUNT(bi.id), 2) as ready_rate_count,
    SUM(bi.amount) as total_amount,
    SUM(CASE WHEN bi.ready_status = 'READY' THEN bi.amount ELSE 0 END) as ready_amount,
    ROUND(SUM(CASE WHEN bi.ready_status = 'READY' THEN bi.amount ELSE 0 END) * 100.0 / NULLIF(SUM(bi.amount), 0), 2) as ready_rate_amount
FROM bom_versions bv
LEFT JOIN bom_items bi ON bv.id = bi.bom_version_id
WHERE bv.is_current = 1
GROUP BY bv.id;

-- 采购订单统计视图
CREATE OR REPLACE VIEW `v_po_statistics` AS
SELECT
    po.id,
    po.order_no,
    po.supplier_id,
    s.supplier_name,
    po.project_id,
    po.order_date,
    po.required_date,
    po.total_amount,
    po.status,
    SUM(poi.received_qty) as total_received_qty,
    SUM(poi.quantity) as total_order_qty,
    ROUND(SUM(poi.received_qty) * 100.0 / NULLIF(SUM(poi.quantity), 0), 2) as receive_rate
FROM purchase_orders po
LEFT JOIN suppliers s ON po.supplier_id = s.id
LEFT JOIN purchase_order_items poi ON po.id = poi.order_id
GROUP BY po.id;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================
-- 完成
-- ============================================
