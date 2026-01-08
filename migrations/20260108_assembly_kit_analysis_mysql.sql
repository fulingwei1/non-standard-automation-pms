-- ============================================
-- 基于装配工艺路径的智能齐套分析系统 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-08
-- 说明: 实现按装配阶段的分层齐套率计算
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. 装配阶段定义表
-- ============================================

CREATE TABLE IF NOT EXISTS `mes_assembly_stage` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `stage_code`          VARCHAR(20) NOT NULL UNIQUE COMMENT '阶段编码',
    `stage_name`          VARCHAR(50) NOT NULL COMMENT '阶段名称',
    `stage_order`         INT NOT NULL COMMENT '阶段顺序(1-6)',
    `description`         TEXT COMMENT '阶段描述',
    `default_duration`    INT DEFAULT 0 COMMENT '默认工期(小时)',
    `color_code`          VARCHAR(20) DEFAULT NULL COMMENT '显示颜色',
    `icon`                VARCHAR(50) DEFAULT NULL COMMENT '图标',
    `is_active`           TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    KEY `idx_assembly_stage_order` (`stage_order`),
    KEY `idx_assembly_stage_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='装配阶段定义表';

-- 初始化6个装配阶段
INSERT IGNORE INTO `mes_assembly_stage` (`stage_code`, `stage_name`, `stage_order`, `description`, `default_duration`, `color_code`, `icon`) VALUES
('FRAME', '框架装配', 1, '铝型材框架搭建、钣金底座组装、立柱安装', 24, '#3B82F6', 'Box'),
('MECH', '机械模组', 2, '直线模组、气缸、电机、导轨滑块、夹具安装', 40, '#10B981', 'Cog'),
('ELECTRIC', '电气安装', 3, 'PLC、伺服驱动、传感器、HMI、电源安装接线', 32, '#F59E0B', 'Zap'),
('WIRING', '线路整理', 4, '线槽安装、线缆整理、标签粘贴、端子接线', 16, '#EF4444', 'Cable'),
('DEBUG', '调试准备', 5, '工装治具准备、测试产品准备、程序调试', 24, '#8B5CF6', 'Bug'),
('COSMETIC', '外观完善', 6, '铭牌、盖板、安全防护、亚克力板安装', 8, '#6B7280', 'Sparkles');

-- ============================================
-- 2. 装配工艺模板表
-- ============================================

CREATE TABLE IF NOT EXISTS `mes_assembly_template` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `template_code`       VARCHAR(50) NOT NULL UNIQUE COMMENT '模板编码',
    `template_name`       VARCHAR(200) NOT NULL COMMENT '模板名称',
    `equipment_type`      VARCHAR(50) NOT NULL COMMENT '设备类型',
    `description`         TEXT COMMENT '模板描述',
    `stage_config`        JSON COMMENT '阶段配置',
    `is_default`          TINYINT(1) DEFAULT 0 COMMENT '是否默认模板',
    `is_active`           TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    `created_by`          INT UNSIGNED DEFAULT NULL COMMENT '创建人ID',
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    KEY `idx_assembly_template_type` (`equipment_type`),
    KEY `idx_assembly_template_active` (`is_active`),
    CONSTRAINT `fk_assembly_template_user` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='装配工艺模板表';

-- ============================================
-- 3. 物料分类与装配阶段映射表
-- ============================================

CREATE TABLE IF NOT EXISTS `mes_category_stage_mapping` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `category_id`         INT UNSIGNED DEFAULT NULL COMMENT '物料分类ID',
    `category_code`       VARCHAR(50) NOT NULL COMMENT '物料分类编码/关键词',
    `category_name`       VARCHAR(100) DEFAULT NULL COMMENT '分类名称',
    `stage_code`          VARCHAR(20) NOT NULL COMMENT '默认装配阶段',
    `priority`            INT DEFAULT 50 COMMENT '优先级(1-100)',
    `is_blocking`         TINYINT(1) DEFAULT 0 COMMENT '是否阻塞性物料',
    `can_postpone`        TINYINT(1) DEFAULT 1 COMMENT '是否可后补',
    `importance_level`    VARCHAR(20) DEFAULT 'NORMAL' COMMENT '重要程度',
    `lead_time_buffer`    INT DEFAULT 0 COMMENT '提前期缓冲(天)',
    `keywords`            JSON COMMENT '匹配关键词',
    `remark`              TEXT COMMENT '备注',
    `is_active`           TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    `created_by`          INT UNSIGNED DEFAULT NULL COMMENT '创建人ID',
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    KEY `idx_category_stage_category` (`category_id`),
    KEY `idx_category_stage_stage` (`stage_code`),
    KEY `idx_category_stage_active` (`is_active`),
    CONSTRAINT `fk_category_stage_category` FOREIGN KEY (`category_id`) REFERENCES `material_categories` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_category_stage_user` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='物料分类与装配阶段映射表';

-- ============================================
-- 4. BOM物料装配属性扩展表
-- ============================================

CREATE TABLE IF NOT EXISTS `bom_item_assembly_attrs` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `bom_item_id`         INT UNSIGNED NOT NULL UNIQUE COMMENT 'BOM明细ID',
    `bom_id`              INT UNSIGNED NOT NULL COMMENT 'BOM表头ID',

    -- 装配阶段
    `assembly_stage`      VARCHAR(20) NOT NULL COMMENT '装配阶段',
    `stage_order`         INT DEFAULT 0 COMMENT '阶段内排序',

    -- 重要程度
    `importance_level`    VARCHAR(20) DEFAULT 'NORMAL' COMMENT '重要程度',
    `is_blocking`         TINYINT(1) DEFAULT 0 COMMENT '是否阻塞性',
    `can_postpone`        TINYINT(1) DEFAULT 1 COMMENT '是否可后补',

    -- 时间要求
    `required_before_stage` TINYINT(1) DEFAULT 1 COMMENT '是否需要在阶段开始前到货',
    `lead_time_days`      INT DEFAULT 0 COMMENT '提前期要求(天)',

    -- 替代信息
    `has_substitute`      TINYINT(1) DEFAULT 0 COMMENT '是否有替代料',
    `substitute_material_ids` JSON COMMENT '替代物料ID列表',

    -- 备注
    `assembly_remark`     TEXT COMMENT '装配备注',

    -- 设置来源
    `setting_source`      VARCHAR(20) DEFAULT 'AUTO' COMMENT '设置来源',

    -- 审核
    `confirmed`           TINYINT(1) DEFAULT 0 COMMENT '是否已确认',
    `confirmed_by`        INT UNSIGNED DEFAULT NULL COMMENT '确认人ID',
    `confirmed_at`        DATETIME DEFAULT NULL COMMENT '确认时间',

    `created_by`          INT UNSIGNED DEFAULT NULL COMMENT '创建人ID',
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    KEY `idx_bom_assembly_bom` (`bom_id`),
    KEY `idx_bom_assembly_stage` (`assembly_stage`),
    KEY `idx_bom_assembly_blocking` (`is_blocking`),
    KEY `idx_bom_assembly_importance` (`importance_level`),
    CONSTRAINT `fk_bom_assembly_item` FOREIGN KEY (`bom_item_id`) REFERENCES `bom_items` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_bom_assembly_header` FOREIGN KEY (`bom_id`) REFERENCES `bom_headers` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_bom_assembly_confirmed_by` FOREIGN KEY (`confirmed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_bom_assembly_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='BOM物料装配属性扩展表';

-- ============================================
-- 5. 齐套分析结果表
-- ============================================

CREATE TABLE IF NOT EXISTS `mes_material_readiness` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `readiness_no`        VARCHAR(50) NOT NULL UNIQUE COMMENT '分析单号',

    -- 分析对象
    `project_id`          INT UNSIGNED NOT NULL COMMENT '项目ID',
    `machine_id`          INT UNSIGNED DEFAULT NULL COMMENT '机台ID',
    `bom_id`              INT UNSIGNED DEFAULT NULL COMMENT 'BOM ID',

    -- 计划信息
    `planned_start_date`  DATE DEFAULT NULL COMMENT '计划开工日期',
    `target_stage`        VARCHAR(20) DEFAULT NULL COMMENT '目标分析阶段',

    -- 整体齐套率
    `overall_kit_rate`    DECIMAL(5,2) DEFAULT 0 COMMENT '整体齐套率(%)',
    `blocking_kit_rate`   DECIMAL(5,2) DEFAULT 0 COMMENT '阻塞性齐套率(%)',

    -- 分阶段齐套率
    `stage_kit_rates`     JSON COMMENT '各阶段齐套率',

    -- 统计数据
    `total_items`         INT DEFAULT 0 COMMENT '物料总项数',
    `fulfilled_items`     INT DEFAULT 0 COMMENT '已齐套项数',
    `shortage_items`      INT DEFAULT 0 COMMENT '缺料项数',
    `in_transit_items`    INT DEFAULT 0 COMMENT '在途项数',
    `blocking_total`      INT DEFAULT 0 COMMENT '阻塞性物料总数',
    `blocking_fulfilled`  INT DEFAULT 0 COMMENT '阻塞性已齐套数',

    -- 金额统计
    `total_amount`        DECIMAL(14,2) DEFAULT 0 COMMENT '物料总金额',
    `shortage_amount`     DECIMAL(14,2) DEFAULT 0 COMMENT '缺料金额',

    -- 分析结果
    `can_start`           TINYINT(1) DEFAULT 0 COMMENT '是否可开工',
    `current_workable_stage` VARCHAR(20) DEFAULT NULL COMMENT '当前可进行到的阶段',
    `first_blocked_stage` VARCHAR(20) DEFAULT NULL COMMENT '首个阻塞阶段',
    `estimated_ready_date` DATE DEFAULT NULL COMMENT '预计完全齐套日期',

    -- 分析信息
    `analysis_time`       DATETIME NOT NULL COMMENT '分析时间',
    `analysis_type`       VARCHAR(20) DEFAULT 'AUTO' COMMENT '分析类型',
    `analyzed_by`         INT UNSIGNED DEFAULT NULL COMMENT '分析人ID',

    -- 状态
    `status`              VARCHAR(20) DEFAULT 'DRAFT' COMMENT '状态',
    `confirmed_by`        INT UNSIGNED DEFAULT NULL COMMENT '确认人ID',
    `confirmed_at`        DATETIME DEFAULT NULL COMMENT '确认时间',
    `expired_at`          DATETIME DEFAULT NULL COMMENT '过期时间',

    `remark`              TEXT COMMENT '备注',
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    KEY `idx_readiness_no` (`readiness_no`),
    KEY `idx_readiness_project` (`project_id`),
    KEY `idx_readiness_machine` (`machine_id`),
    KEY `idx_readiness_bom` (`bom_id`),
    KEY `idx_readiness_status` (`status`),
    KEY `idx_readiness_time` (`analysis_time`),
    KEY `idx_readiness_can_start` (`can_start`),
    CONSTRAINT `fk_readiness_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_readiness_machine` FOREIGN KEY (`machine_id`) REFERENCES `machines` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_readiness_bom` FOREIGN KEY (`bom_id`) REFERENCES `bom_headers` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_readiness_analyzed_by` FOREIGN KEY (`analyzed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_readiness_confirmed_by` FOREIGN KEY (`confirmed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='齐套分析结果表';

-- ============================================
-- 6. 缺料明细表
-- ============================================

CREATE TABLE IF NOT EXISTS `mes_shortage_detail` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `readiness_id`        INT UNSIGNED NOT NULL COMMENT '齐套分析ID',
    `bom_item_id`         INT UNSIGNED NOT NULL COMMENT 'BOM明细ID',

    -- 物料信息
    `material_id`         INT UNSIGNED DEFAULT NULL COMMENT '物料ID',
    `material_code`       VARCHAR(50) NOT NULL COMMENT '物料编码',
    `material_name`       VARCHAR(200) NOT NULL COMMENT '物料名称',
    `specification`       VARCHAR(500) DEFAULT NULL COMMENT '规格型号',
    `unit`                VARCHAR(20) DEFAULT NULL COMMENT '单位',

    -- 装配阶段属性
    `assembly_stage`      VARCHAR(20) NOT NULL COMMENT '所属装配阶段',
    `is_blocking`         TINYINT(1) DEFAULT 0 COMMENT '是否阻塞性',
    `can_postpone`        TINYINT(1) DEFAULT 1 COMMENT '是否可后补',
    `importance_level`    VARCHAR(20) DEFAULT 'NORMAL' COMMENT '重要程度',

    -- 数量信息
    `required_qty`        DECIMAL(12,4) NOT NULL COMMENT '需求数量',
    `stock_qty`           DECIMAL(12,4) DEFAULT 0 COMMENT '库存数量',
    `allocated_qty`       DECIMAL(12,4) DEFAULT 0 COMMENT '已分配',
    `in_transit_qty`      DECIMAL(12,4) DEFAULT 0 COMMENT '在途数量',
    `available_qty`       DECIMAL(12,4) DEFAULT 0 COMMENT '可用数量',
    `shortage_qty`        DECIMAL(12,4) DEFAULT 0 COMMENT '缺料数量',

    -- 金额
    `unit_price`          DECIMAL(12,4) DEFAULT 0 COMMENT '单价',
    `shortage_amount`     DECIMAL(14,2) DEFAULT 0 COMMENT '缺料金额',

    -- 时间
    `required_date`       DATE DEFAULT NULL COMMENT '需求日期',
    `expected_arrival`    DATE DEFAULT NULL COMMENT '预计到货日期',
    `delay_days`          INT DEFAULT 0 COMMENT '预计延误天数',

    -- 采购信息
    `purchase_order_id`   INT UNSIGNED DEFAULT NULL COMMENT '关联采购订单ID',
    `purchase_order_no`   VARCHAR(50) DEFAULT NULL COMMENT '关联采购订单号',
    `supplier_id`         INT UNSIGNED DEFAULT NULL COMMENT '供应商ID',
    `supplier_name`       VARCHAR(200) DEFAULT NULL COMMENT '供应商名称',

    -- 状态
    `shortage_status`     VARCHAR(20) DEFAULT 'OPEN' COMMENT '缺料状态',

    -- 预警
    `alert_level`         VARCHAR(20) DEFAULT NULL COMMENT '预警级别',
    `alert_time`          DATETIME DEFAULT NULL COMMENT '预警时间',

    -- 处理
    `handler_id`          INT UNSIGNED DEFAULT NULL COMMENT '处理人ID',
    `handle_note`         TEXT COMMENT '处理说明',
    `handled_at`          DATETIME DEFAULT NULL COMMENT '处理时间',

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    KEY `idx_shortage_detail_readiness` (`readiness_id`),
    KEY `idx_shortage_detail_material` (`material_code`),
    KEY `idx_shortage_detail_stage` (`assembly_stage`),
    KEY `idx_shortage_detail_blocking` (`is_blocking`),
    KEY `idx_shortage_detail_status` (`shortage_status`),
    KEY `idx_shortage_detail_alert` (`alert_level`),
    CONSTRAINT `fk_shortage_readiness` FOREIGN KEY (`readiness_id`) REFERENCES `mes_material_readiness` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_shortage_bom_item` FOREIGN KEY (`bom_item_id`) REFERENCES `bom_items` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_shortage_material` FOREIGN KEY (`material_id`) REFERENCES `materials` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_shortage_po` FOREIGN KEY (`purchase_order_id`) REFERENCES `purchase_orders` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_shortage_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_shortage_handler` FOREIGN KEY (`handler_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='缺料明细表';

-- ============================================
-- 7. 缺料预警规则配置表
-- ============================================

CREATE TABLE IF NOT EXISTS `mes_shortage_alert_rule` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `rule_code`           VARCHAR(50) NOT NULL UNIQUE COMMENT '规则编码',
    `rule_name`           VARCHAR(200) NOT NULL COMMENT '规则名称',

    -- 预警级别
    `alert_level`         VARCHAR(10) NOT NULL COMMENT '预警级别',

    -- 触发条件
    `days_before_required` INT NOT NULL COMMENT '距需求日期天数',
    `only_blocking`       TINYINT(1) DEFAULT 0 COMMENT '仅阻塞性物料',
    `importance_levels`   JSON COMMENT '适用重要程度',
    `min_shortage_amount` DECIMAL(14,2) DEFAULT 0 COMMENT '最小缺料金额',

    -- 预警动作
    `notify_roles`        JSON COMMENT '通知角色',
    `notify_channels`     JSON COMMENT '通知渠道',
    `auto_escalate`       TINYINT(1) DEFAULT 0 COMMENT '是否自动升级',
    `escalate_after_hours` INT DEFAULT 0 COMMENT '超时后自动升级(小时)',
    `escalate_to_level`   VARCHAR(10) DEFAULT NULL COMMENT '升级到的级别',

    -- 响应要求
    `response_deadline_hours` INT DEFAULT 24 COMMENT '响应时限(小时)',

    -- 排序和启用
    `priority`            INT DEFAULT 50 COMMENT '优先级',
    `is_active`           TINYINT(1) DEFAULT 1 COMMENT '是否启用',

    `description`         TEXT COMMENT '规则描述',
    `created_by`          INT UNSIGNED DEFAULT NULL COMMENT '创建人ID',
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    KEY `idx_alert_rule_level` (`alert_level`),
    KEY `idx_alert_rule_active` (`is_active`),
    KEY `idx_alert_rule_priority` (`priority`),
    CONSTRAINT `fk_alert_rule_user` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='缺料预警规则配置表';

-- 初始化四级预警规则
INSERT IGNORE INTO `mes_shortage_alert_rule` (`rule_code`, `rule_name`, `alert_level`, `days_before_required`, `only_blocking`, `response_deadline_hours`, `priority`, `notify_roles`, `notify_channels`, `auto_escalate`, `escalate_after_hours`, `escalate_to_level`, `description`) VALUES
('L1_STOPPAGE', '停工预警', 'L1', 0, 1, 2, 10,
 '["procurement_manager","project_manager","production_manager"]',
 '["SYSTEM","WECHAT","SMS"]',
 0, 0, NULL,
 '阻塞性物料缺料导致无法装配，需立即处理，2小时内响应'),
('L2_URGENT', '紧急预警', 'L2', 3, 1, 8, 20,
 '["procurement_engineer","project_manager"]',
 '["SYSTEM","WECHAT"]',
 1, 24, 'L1',
 '阻塞性物料3天内需要但缺料，紧急跟进，8小时内响应，24小时未处理升级'),
('L3_ADVANCE', '提前预警', 'L3', 7, 0, 24, 30,
 '["procurement_engineer"]',
 '["SYSTEM","EMAIL"]',
 1, 48, 'L2',
 '物料7天内需要但缺料，提前准备，24小时内响应，48小时未处理升级'),
('L4_NORMAL', '常规预警', 'L4', 14, 0, 48, 40,
 '["procurement_engineer"]',
 '["SYSTEM"]',
 1, 72, 'L3',
 '物料14天内需要但缺料，常规跟进，48小时内响应，72小时未处理升级');

-- ============================================
-- 8. 排产建议表
-- ============================================

CREATE TABLE IF NOT EXISTS `mes_scheduling_suggestion` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `suggestion_no`       VARCHAR(50) NOT NULL UNIQUE COMMENT '建议单号',

    -- 关联
    `readiness_id`        INT UNSIGNED DEFAULT NULL COMMENT '关联齐套分析ID',
    `project_id`          INT UNSIGNED NOT NULL COMMENT '项目ID',
    `machine_id`          INT UNSIGNED DEFAULT NULL COMMENT '机台ID',

    -- 建议类型
    `suggestion_type`     VARCHAR(20) NOT NULL COMMENT '建议类型',

    -- 建议内容
    `suggestion_title`    VARCHAR(200) NOT NULL COMMENT '建议标题',
    `suggestion_content`  TEXT NOT NULL COMMENT '建议详情',

    -- 优先级评分
    `priority_score`      DECIMAL(5,2) DEFAULT 0 COMMENT '优先级得分(0-100)',

    -- 评分因素
    `factors`             JSON COMMENT '影响因素',

    -- 时间建议
    `suggested_start_date` DATE DEFAULT NULL COMMENT '建议开工日期',
    `original_start_date` DATE DEFAULT NULL COMMENT '原计划开工日期',
    `delay_days`          INT DEFAULT 0 COMMENT '建议延期天数',

    -- 影响评估
    `impact_description`  TEXT COMMENT '影响描述',
    `risk_level`          VARCHAR(20) DEFAULT NULL COMMENT '风险级别',

    -- 状态
    `status`              VARCHAR(20) DEFAULT 'PENDING' COMMENT '状态',
    `accepted_by`         INT UNSIGNED DEFAULT NULL COMMENT '接受人ID',
    `accepted_at`         DATETIME DEFAULT NULL COMMENT '接受时间',
    `reject_reason`       TEXT COMMENT '拒绝原因',

    -- 生成信息
    `generated_at`        DATETIME NOT NULL COMMENT '生成时间',
    `valid_until`         DATETIME DEFAULT NULL COMMENT '有效期至',

    `remark`              TEXT COMMENT '备注',
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    KEY `idx_suggestion_no` (`suggestion_no`),
    KEY `idx_suggestion_project` (`project_id`),
    KEY `idx_suggestion_machine` (`machine_id`),
    KEY `idx_suggestion_status` (`status`),
    KEY `idx_suggestion_priority` (`priority_score` DESC),
    KEY `idx_suggestion_type` (`suggestion_type`),
    CONSTRAINT `fk_suggestion_readiness` FOREIGN KEY (`readiness_id`) REFERENCES `mes_material_readiness` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_suggestion_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_suggestion_machine` FOREIGN KEY (`machine_id`) REFERENCES `machines` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_suggestion_accepted_by` FOREIGN KEY (`accepted_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='排产建议表';

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================
-- 完成
-- ============================================
