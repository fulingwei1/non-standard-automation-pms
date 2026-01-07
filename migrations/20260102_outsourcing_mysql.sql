-- ============================================
-- 外协管理模块 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-02
-- 说明: 外协商、外协订单、交付跟踪、质检等
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. 外协商表
-- ============================================

CREATE TABLE IF NOT EXISTS `outsourcing_vendors` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `vendor_code`         VARCHAR(50) NOT NULL COMMENT '外协商编码',
    `vendor_name`         VARCHAR(200) NOT NULL COMMENT '外协商名称',
    `vendor_short_name`   VARCHAR(50) DEFAULT NULL COMMENT '简称',
    `vendor_type`         VARCHAR(20) NOT NULL COMMENT 'MACHINING/ASSEMBLY/SURFACE/ELECTRICAL/OTHER',

    -- 联系信息
    `contact_person`      VARCHAR(50) DEFAULT NULL COMMENT '联系人',
    `contact_phone`       VARCHAR(30) DEFAULT NULL COMMENT '联系电话',
    `contact_email`       VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    `address`             VARCHAR(500) DEFAULT NULL COMMENT '地址',

    -- 资质信息
    `business_license`    VARCHAR(100) DEFAULT NULL COMMENT '营业执照号',
    `qualification`       JSON DEFAULT NULL COMMENT '资质认证',
    `capabilities`        JSON DEFAULT NULL COMMENT '加工能力',

    -- 评价
    `quality_rating`      DECIMAL(3,2) DEFAULT 0 COMMENT '质量评分(0-5)',
    `delivery_rating`     DECIMAL(3,2) DEFAULT 0 COMMENT '交期评分(0-5)',
    `service_rating`      DECIMAL(3,2) DEFAULT 0 COMMENT '服务评分(0-5)',
    `overall_rating`      DECIMAL(3,2) DEFAULT 0 COMMENT '综合评分',

    -- 状态
    `status`              VARCHAR(20) DEFAULT 'ACTIVE' COMMENT 'ACTIVE/INACTIVE/BLACKLIST',
    `cooperation_start`   DATE DEFAULT NULL COMMENT '合作开始日期',
    `last_order_date`     DATE DEFAULT NULL COMMENT '最后订单日期',

    -- 银行信息
    `bank_name`           VARCHAR(100) DEFAULT NULL COMMENT '开户行',
    `bank_account`        VARCHAR(50) DEFAULT NULL COMMENT '银行账号',
    `tax_number`          VARCHAR(50) DEFAULT NULL COMMENT '税号',

    `remark`              TEXT DEFAULT NULL,

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_vendor_code` (`vendor_code`),
    KEY `idx_vendors_type` (`vendor_type`),
    KEY `idx_vendors_status` (`status`),
    CONSTRAINT `fk_vendors_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外协商表';

-- ============================================
-- 2. 外协订单表
-- ============================================

CREATE TABLE IF NOT EXISTS `outsourcing_orders` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `order_no`            VARCHAR(50) NOT NULL COMMENT '外协订单号',
    `vendor_id`           INT UNSIGNED NOT NULL COMMENT '外协商ID',
    `project_id`          INT UNSIGNED NOT NULL COMMENT '项目ID',
    `machine_id`          INT UNSIGNED DEFAULT NULL COMMENT '设备ID',

    -- 订单信息
    `order_type`          VARCHAR(20) NOT NULL COMMENT 'MACHINING/ASSEMBLY/SURFACE/OTHER',
    `order_title`         VARCHAR(200) NOT NULL COMMENT '订单标题',
    `order_description`   TEXT DEFAULT NULL COMMENT '订单说明',

    -- 金额
    `total_amount`        DECIMAL(14,2) DEFAULT 0 COMMENT '总金额',
    `tax_rate`            DECIMAL(5,2) DEFAULT 13 COMMENT '税率',
    `tax_amount`          DECIMAL(14,2) DEFAULT 0 COMMENT '税额',
    `amount_with_tax`     DECIMAL(14,2) DEFAULT 0 COMMENT '含税金额',

    -- 时间要求
    `required_date`       DATE DEFAULT NULL COMMENT '要求交期',
    `estimated_date`      DATE DEFAULT NULL COMMENT '预计交期',
    `actual_date`         DATE DEFAULT NULL COMMENT '实际交期',

    -- 状态
    `status`              VARCHAR(20) DEFAULT 'DRAFT' COMMENT '状态',

    -- 付款状态
    `payment_status`      VARCHAR(20) DEFAULT 'UNPAID' COMMENT 'UNPAID/PARTIAL/PAID',
    `paid_amount`         DECIMAL(14,2) DEFAULT 0 COMMENT '已付金额',

    -- 签约
    `contract_no`         VARCHAR(100) DEFAULT NULL COMMENT '合同编号',
    `contract_file`       VARCHAR(500) DEFAULT NULL COMMENT '合同文件路径',

    `remark`              TEXT DEFAULT NULL,

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_order_no` (`order_no`),
    KEY `idx_orders_vendor` (`vendor_id`),
    KEY `idx_orders_project` (`project_id`),
    KEY `idx_orders_status` (`status`),
    CONSTRAINT `fk_os_orders_vendor` FOREIGN KEY (`vendor_id`) REFERENCES `outsourcing_vendors` (`id`),
    CONSTRAINT `fk_os_orders_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_os_orders_machine` FOREIGN KEY (`machine_id`) REFERENCES `machines` (`id`),
    CONSTRAINT `fk_os_orders_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外协订单表';

-- ============================================
-- 3. 外协订单明细表
-- ============================================

CREATE TABLE IF NOT EXISTS `outsourcing_order_items` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `order_id`            INT UNSIGNED NOT NULL COMMENT '外协订单ID',
    `item_no`             INT NOT NULL COMMENT '行号',

    -- 物料信息
    `material_id`         INT UNSIGNED DEFAULT NULL COMMENT '物料ID',
    `material_code`       VARCHAR(50) NOT NULL COMMENT '物料编码',
    `material_name`       VARCHAR(200) NOT NULL COMMENT '物料名称',
    `specification`       VARCHAR(500) DEFAULT NULL COMMENT '规格型号',
    `drawing_no`          VARCHAR(100) DEFAULT NULL COMMENT '图号',

    -- 加工信息
    `process_type`        VARCHAR(50) DEFAULT NULL COMMENT '加工类型',
    `process_content`     TEXT DEFAULT NULL COMMENT '加工内容',
    `process_requirements` TEXT DEFAULT NULL COMMENT '工艺要求',

    -- 数量与单价
    `unit`                VARCHAR(20) DEFAULT '件' COMMENT '单位',
    `quantity`            DECIMAL(10,4) NOT NULL COMMENT '数量',
    `unit_price`          DECIMAL(12,4) DEFAULT 0 COMMENT '单价',
    `amount`              DECIMAL(14,2) DEFAULT 0 COMMENT '金额',

    -- 来料信息
    `material_provided`   TINYINT(1) DEFAULT 0 COMMENT '是否来料加工',
    `provided_quantity`   DECIMAL(10,4) DEFAULT 0 COMMENT '来料数量',
    `provided_date`       DATE DEFAULT NULL COMMENT '来料日期',

    -- 交付信息
    `delivered_quantity`  DECIMAL(10,4) DEFAULT 0 COMMENT '已交付数量',
    `qualified_quantity`  DECIMAL(10,4) DEFAULT 0 COMMENT '合格数量',
    `rejected_quantity`   DECIMAL(10,4) DEFAULT 0 COMMENT '不合格数量',

    -- 状态
    `status`              VARCHAR(20) DEFAULT 'PENDING' COMMENT '状态',

    `remark`              TEXT DEFAULT NULL,

    PRIMARY KEY (`id`),
    KEY `idx_items_order` (`order_id`),
    KEY `idx_items_material` (`material_id`),
    CONSTRAINT `fk_os_items_order` FOREIGN KEY (`order_id`) REFERENCES `outsourcing_orders` (`id`),
    CONSTRAINT `fk_os_items_material` FOREIGN KEY (`material_id`) REFERENCES `materials` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外协订单明细表';

-- ============================================
-- 4. 外协交付记录表
-- ============================================

CREATE TABLE IF NOT EXISTS `outsourcing_deliveries` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `delivery_no`         VARCHAR(50) NOT NULL COMMENT '交付单号',
    `order_id`            INT UNSIGNED NOT NULL COMMENT '外协订单ID',
    `vendor_id`           INT UNSIGNED NOT NULL COMMENT '外协商ID',

    -- 交付信息
    `delivery_date`       DATE NOT NULL COMMENT '交付日期',
    `delivery_type`       VARCHAR(20) DEFAULT 'NORMAL' COMMENT 'NORMAL/PARTIAL/FINAL',
    `delivery_person`     VARCHAR(50) DEFAULT NULL COMMENT '送货人',
    `receiver`            VARCHAR(50) DEFAULT NULL COMMENT '收货人',

    -- 物流信息
    `logistics_company`   VARCHAR(100) DEFAULT NULL COMMENT '物流公司',
    `tracking_no`         VARCHAR(100) DEFAULT NULL COMMENT '运单号',

    -- 状态
    `status`              VARCHAR(20) DEFAULT 'PENDING' COMMENT 'PENDING/RECEIVED/INSPECTING/COMPLETED',
    `received_at`         DATETIME DEFAULT NULL COMMENT '收货时间',
    `received_by`         INT UNSIGNED DEFAULT NULL COMMENT '收货人ID',

    `remark`              TEXT DEFAULT NULL,

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_delivery_no` (`delivery_no`),
    KEY `idx_deliveries_order` (`order_id`),
    KEY `idx_deliveries_vendor` (`vendor_id`),
    KEY `idx_deliveries_status` (`status`),
    CONSTRAINT `fk_deliveries_order` FOREIGN KEY (`order_id`) REFERENCES `outsourcing_orders` (`id`),
    CONSTRAINT `fk_deliveries_vendor` FOREIGN KEY (`vendor_id`) REFERENCES `outsourcing_vendors` (`id`),
    CONSTRAINT `fk_deliveries_received_by` FOREIGN KEY (`received_by`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_deliveries_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外协交付记录表';

-- ============================================
-- 5. 外协交付明细表
-- ============================================

CREATE TABLE IF NOT EXISTS `outsourcing_delivery_items` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `delivery_id`         INT UNSIGNED NOT NULL COMMENT '交付单ID',
    `order_item_id`       INT UNSIGNED NOT NULL COMMENT '订单明细ID',

    -- 物料信息
    `material_code`       VARCHAR(50) NOT NULL,
    `material_name`       VARCHAR(200) NOT NULL,

    -- 数量
    `delivery_quantity`   DECIMAL(10,4) NOT NULL COMMENT '交付数量',
    `received_quantity`   DECIMAL(10,4) DEFAULT 0 COMMENT '实收数量',

    -- 质检结果
    `inspect_status`      VARCHAR(20) DEFAULT 'PENDING' COMMENT '质检状态',
    `qualified_quantity`  DECIMAL(10,4) DEFAULT 0 COMMENT '合格数量',
    `rejected_quantity`   DECIMAL(10,4) DEFAULT 0 COMMENT '不合格数量',

    `remark`              TEXT DEFAULT NULL,

    PRIMARY KEY (`id`),
    KEY `idx_delivery_items_delivery` (`delivery_id`),
    CONSTRAINT `fk_delivery_items_delivery` FOREIGN KEY (`delivery_id`) REFERENCES `outsourcing_deliveries` (`id`),
    CONSTRAINT `fk_delivery_items_order_item` FOREIGN KEY (`order_item_id`) REFERENCES `outsourcing_order_items` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外协交付明细表';

-- ============================================
-- 6. 外协质检记录表
-- ============================================

CREATE TABLE IF NOT EXISTS `outsourcing_inspections` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `inspection_no`       VARCHAR(50) NOT NULL COMMENT '质检单号',
    `delivery_id`         INT UNSIGNED NOT NULL COMMENT '交付单ID',
    `delivery_item_id`    INT UNSIGNED NOT NULL COMMENT '交付明细ID',

    -- 质检信息
    `inspect_type`        VARCHAR(20) DEFAULT 'INCOMING' COMMENT 'INCOMING/PROCESS/FINAL',
    `inspect_date`        DATE NOT NULL COMMENT '质检日期',
    `inspector_id`        INT UNSIGNED DEFAULT NULL COMMENT '质检员ID',
    `inspector_name`      VARCHAR(50) DEFAULT NULL COMMENT '质检员姓名',

    -- 检验数量
    `inspect_quantity`    DECIMAL(10,4) NOT NULL COMMENT '送检数量',
    `sample_quantity`     DECIMAL(10,4) DEFAULT 0 COMMENT '抽检数量',
    `qualified_quantity`  DECIMAL(10,4) DEFAULT 0 COMMENT '合格数量',
    `rejected_quantity`   DECIMAL(10,4) DEFAULT 0 COMMENT '不合格数量',

    -- 结果
    `inspect_result`      VARCHAR(20) DEFAULT NULL COMMENT 'PASSED/REJECTED/CONDITIONAL',
    `pass_rate`           DECIMAL(5,2) DEFAULT 0 COMMENT '合格率',

    -- 不良信息
    `defect_description`  TEXT DEFAULT NULL COMMENT '不良描述',
    `defect_type`         VARCHAR(50) DEFAULT NULL COMMENT '不良类型',
    `defect_images`       JSON DEFAULT NULL COMMENT '不良图片',

    -- 处理
    `disposition`         VARCHAR(20) DEFAULT NULL COMMENT 'ACCEPT/REWORK/RETURN/SCRAP',
    `disposition_note`    TEXT DEFAULT NULL COMMENT '处理说明',

    `remark`              TEXT DEFAULT NULL,

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_inspection_no` (`inspection_no`),
    KEY `idx_inspections_delivery` (`delivery_id`),
    KEY `idx_inspections_result` (`inspect_result`),
    CONSTRAINT `fk_inspections_delivery` FOREIGN KEY (`delivery_id`) REFERENCES `outsourcing_deliveries` (`id`),
    CONSTRAINT `fk_inspections_delivery_item` FOREIGN KEY (`delivery_item_id`) REFERENCES `outsourcing_delivery_items` (`id`),
    CONSTRAINT `fk_inspections_inspector` FOREIGN KEY (`inspector_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外协质检记录表';

-- ============================================
-- 7. 外协付款记录表
-- ============================================

CREATE TABLE IF NOT EXISTS `outsourcing_payments` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `payment_no`          VARCHAR(50) NOT NULL COMMENT '付款单号',
    `vendor_id`           INT UNSIGNED NOT NULL COMMENT '外协商ID',
    `order_id`            INT UNSIGNED DEFAULT NULL COMMENT '外协订单ID',

    -- 付款信息
    `payment_type`        VARCHAR(20) NOT NULL COMMENT 'ADVANCE/PROGRESS/FINAL/SETTLEMENT',
    `payment_amount`      DECIMAL(14,2) NOT NULL COMMENT '付款金额',
    `payment_date`        DATE DEFAULT NULL COMMENT '付款日期',
    `payment_method`      VARCHAR(20) DEFAULT NULL COMMENT 'BANK/CASH/CHECK',

    -- 发票信息
    `invoice_no`          VARCHAR(100) DEFAULT NULL COMMENT '发票号',
    `invoice_amount`      DECIMAL(14,2) DEFAULT NULL COMMENT '发票金额',
    `invoice_date`        DATE DEFAULT NULL COMMENT '发票日期',

    -- 审批
    `status`              VARCHAR(20) DEFAULT 'DRAFT' COMMENT 'DRAFT/PENDING/APPROVED/PAID/REJECTED',
    `approved_by`         INT UNSIGNED DEFAULT NULL COMMENT '审批人',
    `approved_at`         DATETIME DEFAULT NULL COMMENT '审批时间',

    `remark`              TEXT DEFAULT NULL,

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_payment_no` (`payment_no`),
    KEY `idx_payments_vendor` (`vendor_id`),
    KEY `idx_payments_order` (`order_id`),
    KEY `idx_payments_status` (`status`),
    CONSTRAINT `fk_payments_vendor` FOREIGN KEY (`vendor_id`) REFERENCES `outsourcing_vendors` (`id`),
    CONSTRAINT `fk_payments_order` FOREIGN KEY (`order_id`) REFERENCES `outsourcing_orders` (`id`),
    CONSTRAINT `fk_payments_approved_by` FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_payments_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外协付款记录表';

-- ============================================
-- 8. 外协商评价表
-- ============================================

CREATE TABLE IF NOT EXISTS `outsourcing_evaluations` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `vendor_id`           INT UNSIGNED NOT NULL COMMENT '外协商ID',
    `order_id`            INT UNSIGNED DEFAULT NULL COMMENT '关联订单',
    `eval_period`         VARCHAR(20) DEFAULT NULL COMMENT '评价周期',

    -- 评分(1-5分)
    `quality_score`       DECIMAL(3,2) DEFAULT 0 COMMENT '质量评分',
    `delivery_score`      DECIMAL(3,2) DEFAULT 0 COMMENT '交期评分',
    `price_score`         DECIMAL(3,2) DEFAULT 0 COMMENT '价格评分',
    `service_score`       DECIMAL(3,2) DEFAULT 0 COMMENT '服务评分',
    `overall_score`       DECIMAL(3,2) DEFAULT 0 COMMENT '综合评分',

    -- 评价内容
    `advantages`          TEXT DEFAULT NULL COMMENT '优点',
    `disadvantages`       TEXT DEFAULT NULL COMMENT '不足',
    `improvement`         TEXT DEFAULT NULL COMMENT '改进建议',

    -- 评价人
    `evaluator_id`        INT UNSIGNED DEFAULT NULL,
    `evaluated_at`        DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_evaluations_vendor` (`vendor_id`),
    KEY `idx_evaluations_period` (`eval_period`),
    CONSTRAINT `fk_evaluations_vendor` FOREIGN KEY (`vendor_id`) REFERENCES `outsourcing_vendors` (`id`),
    CONSTRAINT `fk_evaluations_order` FOREIGN KEY (`order_id`) REFERENCES `outsourcing_orders` (`id`),
    CONSTRAINT `fk_evaluations_evaluator` FOREIGN KEY (`evaluator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外协商评价表';

-- ============================================
-- 9. 外协进度跟踪表
-- ============================================

CREATE TABLE IF NOT EXISTS `outsourcing_progress` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `order_id`            INT UNSIGNED NOT NULL COMMENT '外协订单ID',
    `order_item_id`       INT UNSIGNED DEFAULT NULL COMMENT '订单明细ID',

    -- 进度信息
    `report_date`         DATE NOT NULL COMMENT '报告日期',
    `progress_pct`        INT DEFAULT 0 COMMENT '进度百分比',
    `completed_quantity`  DECIMAL(10,4) DEFAULT 0 COMMENT '完成数量',

    -- 状态
    `current_process`     VARCHAR(100) DEFAULT NULL COMMENT '当前工序',
    `next_process`        VARCHAR(100) DEFAULT NULL COMMENT '下一工序',
    `estimated_complete`  DATE DEFAULT NULL COMMENT '预计完成日期',

    -- 问题
    `issues`              TEXT DEFAULT NULL COMMENT '问题说明',
    `risk_level`          VARCHAR(20) DEFAULT NULL COMMENT 'LOW/MEDIUM/HIGH',

    -- 附件
    `attachments`         JSON DEFAULT NULL COMMENT '附件',

    `reported_by`         INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_progress_order` (`order_id`),
    KEY `idx_progress_date` (`report_date`),
    CONSTRAINT `fk_progress_order` FOREIGN KEY (`order_id`) REFERENCES `outsourcing_orders` (`id`),
    CONSTRAINT `fk_progress_order_item` FOREIGN KEY (`order_item_id`) REFERENCES `outsourcing_order_items` (`id`),
    CONSTRAINT `fk_progress_reported_by` FOREIGN KEY (`reported_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外协进度跟踪表';

-- ============================================
-- 10. 视图定义
-- ============================================

-- 外协订单概览视图
CREATE OR REPLACE VIEW `v_outsourcing_overview` AS
SELECT
    oo.id,
    oo.order_no,
    oo.order_type,
    oo.order_title,
    oo.vendor_id,
    ov.vendor_name,
    oo.project_id,
    p.project_name,
    oo.total_amount,
    oo.amount_with_tax,
    oo.required_date,
    oo.estimated_date,
    oo.actual_date,
    oo.status,
    oo.payment_status,
    oo.paid_amount,
    (SELECT COUNT(*) FROM outsourcing_order_items oi WHERE oi.order_id = oo.id) as item_count,
    (SELECT SUM(delivered_quantity) FROM outsourcing_order_items oi WHERE oi.order_id = oo.id) as total_delivered,
    (SELECT SUM(quantity) FROM outsourcing_order_items oi WHERE oi.order_id = oo.id) as total_quantity
FROM outsourcing_orders oo
LEFT JOIN outsourcing_vendors ov ON oo.vendor_id = ov.id
LEFT JOIN projects p ON oo.project_id = p.id;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================
-- 完成
-- ============================================
