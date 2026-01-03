-- ============================================
-- 验收管理模块 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-02
-- 说明: 验收模板、验收单、检查项、问题、签字等
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. 验收模板表
-- ============================================

CREATE TABLE IF NOT EXISTS `acceptance_templates` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `template_code`       VARCHAR(50) NOT NULL COMMENT '模板编码',
    `template_name`       VARCHAR(200) NOT NULL COMMENT '模板名称',
    `acceptance_type`     VARCHAR(20) NOT NULL COMMENT 'FAT/SAT/FINAL',
    `equipment_type`      VARCHAR(50) DEFAULT NULL COMMENT '设备类型',
    `version`             VARCHAR(20) DEFAULT '1.0' COMMENT '版本号',
    `description`         TEXT DEFAULT NULL COMMENT '模板说明',
    `is_system`           TINYINT(1) DEFAULT 0 COMMENT '是否系统预置',
    `is_active`           TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_template_code` (`template_code`),
    KEY `idx_templates_type` (`acceptance_type`),
    KEY `idx_templates_equip` (`equipment_type`),
    CONSTRAINT `fk_templates_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='验收模板表';

-- ============================================
-- 2. 模板检查分类表
-- ============================================

CREATE TABLE IF NOT EXISTS `template_categories` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `template_id`         INT UNSIGNED NOT NULL COMMENT '所属模板',
    `category_code`       VARCHAR(20) NOT NULL COMMENT '分类编码',
    `category_name`       VARCHAR(100) NOT NULL COMMENT '分类名称',
    `weight`              DECIMAL(5,2) DEFAULT 0 COMMENT '权重百分比',
    `sort_order`          INT DEFAULT 0 COMMENT '排序',
    `is_required`         TINYINT(1) DEFAULT 1 COMMENT '是否必检分类',
    `description`         TEXT DEFAULT NULL COMMENT '分类说明',

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_category` (`template_id`, `category_code`),
    KEY `idx_categories_template` (`template_id`),
    CONSTRAINT `fk_categories_template` FOREIGN KEY (`template_id`) REFERENCES `acceptance_templates` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模板检查分类表';

-- ============================================
-- 3. 模板检查项表
-- ============================================

CREATE TABLE IF NOT EXISTS `template_check_items` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `category_id`         INT UNSIGNED NOT NULL COMMENT '所属分类',
    `item_code`           VARCHAR(50) NOT NULL COMMENT '检查项编码',
    `item_name`           VARCHAR(200) NOT NULL COMMENT '检查项名称',
    `check_method`        TEXT DEFAULT NULL COMMENT '检查方法',
    `acceptance_criteria` TEXT DEFAULT NULL COMMENT '验收标准',
    `standard_value`      VARCHAR(100) DEFAULT NULL COMMENT '标准值',
    `tolerance_min`       VARCHAR(50) DEFAULT NULL COMMENT '下限',
    `tolerance_max`       VARCHAR(50) DEFAULT NULL COMMENT '上限',
    `unit`                VARCHAR(20) DEFAULT NULL COMMENT '单位',
    `is_required`         TINYINT(1) DEFAULT 1 COMMENT '是否必检项',
    `is_key_item`         TINYINT(1) DEFAULT 0 COMMENT '是否关键项',
    `sort_order`          INT DEFAULT 0 COMMENT '排序',

    PRIMARY KEY (`id`),
    KEY `idx_check_items_category` (`category_id`),
    CONSTRAINT `fk_check_items_category` FOREIGN KEY (`category_id`) REFERENCES `template_categories` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模板检查项表';

-- ============================================
-- 4. 验收单表
-- ============================================

CREATE TABLE IF NOT EXISTS `acceptance_orders` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `order_no`            VARCHAR(50) NOT NULL COMMENT '验收单号',
    `project_id`          INT UNSIGNED NOT NULL COMMENT '项目ID',
    `machine_id`          INT UNSIGNED DEFAULT NULL COMMENT '设备ID',
    `acceptance_type`     VARCHAR(20) NOT NULL COMMENT 'FAT/SAT/FINAL',
    `template_id`         INT UNSIGNED DEFAULT NULL COMMENT '使用的模板',

    -- 验收信息
    `planned_date`        DATE DEFAULT NULL COMMENT '计划验收日期',
    `actual_start_date`   DATETIME DEFAULT NULL COMMENT '实际开始时间',
    `actual_end_date`     DATETIME DEFAULT NULL COMMENT '实际结束时间',
    `location`            VARCHAR(200) DEFAULT NULL COMMENT '验收地点',

    -- 状态
    `status`              VARCHAR(20) DEFAULT 'DRAFT' COMMENT '验收状态',

    -- 统计
    `total_items`         INT DEFAULT 0 COMMENT '检查项总数',
    `passed_items`        INT DEFAULT 0 COMMENT '通过项数',
    `failed_items`        INT DEFAULT 0 COMMENT '不通过项数',
    `na_items`            INT DEFAULT 0 COMMENT '不适用项数',
    `pass_rate`           DECIMAL(5,2) DEFAULT 0 COMMENT '通过率',

    -- 结论
    `overall_result`      VARCHAR(20) DEFAULT NULL COMMENT 'PASSED/FAILED/CONDITIONAL',
    `conclusion`          TEXT DEFAULT NULL COMMENT '验收结论',
    `conditions`          TEXT DEFAULT NULL COMMENT '有条件通过的条件说明',

    -- 签字确认
    `qa_signer_id`        INT UNSIGNED DEFAULT NULL COMMENT 'QA签字人',
    `qa_signed_at`        DATETIME DEFAULT NULL COMMENT 'QA签字时间',
    `customer_signer`     VARCHAR(100) DEFAULT NULL COMMENT '客户签字人',
    `customer_signed_at`  DATETIME DEFAULT NULL COMMENT '客户签字时间',
    `customer_signature`  TEXT DEFAULT NULL COMMENT '客户电子签名',

    -- 附件
    `report_file_path`    VARCHAR(500) DEFAULT NULL COMMENT '验收报告文件路径',

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_order_no` (`order_no`),
    KEY `idx_orders_project` (`project_id`),
    KEY `idx_orders_machine` (`machine_id`),
    KEY `idx_orders_status` (`status`),
    KEY `idx_orders_type` (`acceptance_type`),
    CONSTRAINT `fk_orders_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_orders_machine` FOREIGN KEY (`machine_id`) REFERENCES `machines` (`id`),
    CONSTRAINT `fk_orders_template` FOREIGN KEY (`template_id`) REFERENCES `acceptance_templates` (`id`),
    CONSTRAINT `fk_orders_qa_signer` FOREIGN KEY (`qa_signer_id`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_orders_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='验收单表';

-- ============================================
-- 5. 验收单检查项表
-- ============================================

CREATE TABLE IF NOT EXISTS `acceptance_order_items` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `order_id`            INT UNSIGNED NOT NULL COMMENT '验收单ID',
    `template_item_id`    INT UNSIGNED DEFAULT NULL COMMENT '模板检查项ID',

    -- 检查项信息(从模板复制)
    `category_code`       VARCHAR(20) NOT NULL,
    `category_name`       VARCHAR(100) NOT NULL,
    `item_code`           VARCHAR(50) NOT NULL,
    `item_name`           VARCHAR(200) NOT NULL,
    `check_method`        TEXT DEFAULT NULL,
    `acceptance_criteria` TEXT DEFAULT NULL,
    `standard_value`      VARCHAR(100) DEFAULT NULL,
    `tolerance_min`       VARCHAR(50) DEFAULT NULL,
    `tolerance_max`       VARCHAR(50) DEFAULT NULL,
    `unit`                VARCHAR(20) DEFAULT NULL,
    `is_required`         TINYINT(1) DEFAULT 1,
    `is_key_item`         TINYINT(1) DEFAULT 0,
    `sort_order`          INT DEFAULT 0,

    -- 检查结果
    `result_status`       VARCHAR(20) DEFAULT 'PENDING' COMMENT 'PENDING/PASSED/FAILED/NA/CONDITIONAL',
    `actual_value`        VARCHAR(100) DEFAULT NULL COMMENT '实际值',
    `deviation`           VARCHAR(100) DEFAULT NULL COMMENT '偏差',
    `remark`              TEXT DEFAULT NULL COMMENT '备注',

    -- 检查记录
    `checked_by`          INT UNSIGNED DEFAULT NULL COMMENT '检查人',
    `checked_at`          DATETIME DEFAULT NULL COMMENT '检查时间',

    -- 复验信息
    `retry_count`         INT DEFAULT 0 COMMENT '复验次数',
    `last_retry_at`       DATETIME DEFAULT NULL COMMENT '最后复验时间',

    PRIMARY KEY (`id`),
    KEY `idx_order_items_order` (`order_id`),
    KEY `idx_order_items_status` (`result_status`),
    CONSTRAINT `fk_order_items_order` FOREIGN KEY (`order_id`) REFERENCES `acceptance_orders` (`id`),
    CONSTRAINT `fk_order_items_template` FOREIGN KEY (`template_item_id`) REFERENCES `template_check_items` (`id`),
    CONSTRAINT `fk_order_items_checked_by` FOREIGN KEY (`checked_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='验收单检查项表';

-- ============================================
-- 6. 验收问题表
-- ============================================

CREATE TABLE IF NOT EXISTS `acceptance_issues` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `issue_no`            VARCHAR(50) NOT NULL COMMENT '问题编号',
    `order_id`            INT UNSIGNED NOT NULL COMMENT '验收单ID',
    `order_item_id`       INT UNSIGNED DEFAULT NULL COMMENT '关联检查项',

    -- 问题信息
    `issue_type`          VARCHAR(20) NOT NULL COMMENT 'DEFECT/DEVIATION/SUGGESTION',
    `severity`            VARCHAR(20) NOT NULL COMMENT 'CRITICAL/MAJOR/MINOR',
    `title`               VARCHAR(200) NOT NULL COMMENT '问题标题',
    `description`         TEXT NOT NULL COMMENT '问题描述',
    `found_at`            DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '发现时间',
    `found_by`            INT UNSIGNED DEFAULT NULL COMMENT '发现人',

    -- 处理信息
    `status`              VARCHAR(20) DEFAULT 'OPEN' COMMENT 'OPEN/PROCESSING/RESOLVED/CLOSED/DEFERRED',
    `assigned_to`         INT UNSIGNED DEFAULT NULL COMMENT '处理负责人',
    `due_date`            DATE DEFAULT NULL COMMENT '要求完成日期',

    -- 解决信息
    `solution`            TEXT DEFAULT NULL COMMENT '解决方案',
    `resolved_at`         DATETIME DEFAULT NULL COMMENT '解决时间',
    `resolved_by`         INT UNSIGNED DEFAULT NULL COMMENT '解决人',

    -- 验证信息
    `verified_at`         DATETIME DEFAULT NULL COMMENT '验证时间',
    `verified_by`         INT UNSIGNED DEFAULT NULL COMMENT '验证人',
    `verified_result`     VARCHAR(20) DEFAULT NULL COMMENT 'VERIFIED/REJECTED',

    -- 是否阻塞验收
    `is_blocking`         TINYINT(1) DEFAULT 0 COMMENT '是否阻塞验收通过',

    -- 附件
    `attachments`         JSON DEFAULT NULL COMMENT '附件列表',

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_issue_no` (`issue_no`),
    KEY `idx_issues_order` (`order_id`),
    KEY `idx_issues_status` (`status`),
    KEY `idx_issues_severity` (`severity`),
    KEY `idx_issues_assigned` (`assigned_to`),
    CONSTRAINT `fk_issues_order` FOREIGN KEY (`order_id`) REFERENCES `acceptance_orders` (`id`),
    CONSTRAINT `fk_issues_order_item` FOREIGN KEY (`order_item_id`) REFERENCES `acceptance_order_items` (`id`),
    CONSTRAINT `fk_issues_found_by` FOREIGN KEY (`found_by`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_issues_assigned_to` FOREIGN KEY (`assigned_to`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_issues_resolved_by` FOREIGN KEY (`resolved_by`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_issues_verified_by` FOREIGN KEY (`verified_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='验收问题表';

-- ============================================
-- 7. 问题跟进记录表
-- ============================================

CREATE TABLE IF NOT EXISTS `issue_follow_ups` (
    `id`                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `issue_id`            INT UNSIGNED NOT NULL COMMENT '问题ID',
    `action_type`         VARCHAR(20) NOT NULL COMMENT 'COMMENT/STATUS_CHANGE/ASSIGN/RESOLVE/VERIFY',
    `action_content`      TEXT NOT NULL COMMENT '操作内容',
    `old_value`           VARCHAR(100) DEFAULT NULL COMMENT '原值',
    `new_value`           VARCHAR(100) DEFAULT NULL COMMENT '新值',
    `attachments`         JSON DEFAULT NULL COMMENT '附件',
    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_follow_ups_issue` (`issue_id`),
    CONSTRAINT `fk_follow_ups_issue` FOREIGN KEY (`issue_id`) REFERENCES `acceptance_issues` (`id`),
    CONSTRAINT `fk_follow_ups_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问题跟进记录表';

-- ============================================
-- 8. 验收签字记录表
-- ============================================

CREATE TABLE IF NOT EXISTS `acceptance_signatures` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `order_id`            INT UNSIGNED NOT NULL COMMENT '验收单ID',
    `signer_type`         VARCHAR(20) NOT NULL COMMENT 'QA/PM/CUSTOMER/WITNESS',
    `signer_role`         VARCHAR(50) DEFAULT NULL COMMENT '签字人角色',
    `signer_name`         VARCHAR(100) NOT NULL COMMENT '签字人姓名',
    `signer_user_id`      INT UNSIGNED DEFAULT NULL COMMENT '系统用户ID',
    `signer_company`      VARCHAR(200) DEFAULT NULL COMMENT '签字人公司',
    `signature_data`      TEXT DEFAULT NULL COMMENT '电子签名数据',
    `signed_at`           DATETIME DEFAULT CURRENT_TIMESTAMP,
    `ip_address`          VARCHAR(50) DEFAULT NULL COMMENT '签字IP',
    `device_info`         VARCHAR(200) DEFAULT NULL COMMENT '设备信息',

    PRIMARY KEY (`id`),
    KEY `idx_signatures_order` (`order_id`),
    CONSTRAINT `fk_signatures_order` FOREIGN KEY (`order_id`) REFERENCES `acceptance_orders` (`id`),
    CONSTRAINT `fk_signatures_user` FOREIGN KEY (`signer_user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='验收签字记录表';

-- ============================================
-- 9. 验收报告表
-- ============================================

CREATE TABLE IF NOT EXISTS `acceptance_reports` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `order_id`            INT UNSIGNED NOT NULL COMMENT '验收单ID',
    `report_no`           VARCHAR(50) NOT NULL COMMENT '报告编号',
    `report_type`         VARCHAR(20) NOT NULL COMMENT 'DRAFT/OFFICIAL',
    `version`             INT DEFAULT 1 COMMENT '版本号',

    -- 报告内容
    `report_content`      LONGTEXT DEFAULT NULL COMMENT '报告正文',

    -- 文件信息
    `file_path`           VARCHAR(500) DEFAULT NULL COMMENT 'PDF文件路径',
    `file_size`           INT DEFAULT NULL COMMENT '文件大小',
    `file_hash`           VARCHAR(64) DEFAULT NULL COMMENT '文件哈希',

    `generated_at`        DATETIME DEFAULT NULL COMMENT '生成时间',
    `generated_by`        INT UNSIGNED DEFAULT NULL COMMENT '生成人',

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_report_no` (`report_no`),
    KEY `idx_reports_order` (`order_id`),
    CONSTRAINT `fk_reports_order` FOREIGN KEY (`order_id`) REFERENCES `acceptance_orders` (`id`),
    CONSTRAINT `fk_reports_generated_by` FOREIGN KEY (`generated_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='验收报告表';

-- ============================================
-- 10. 视图定义
-- ============================================

-- 验收单概览视图
CREATE OR REPLACE VIEW `v_acceptance_overview` AS
SELECT
    ao.id,
    ao.order_no,
    ao.acceptance_type,
    ao.project_id,
    p.project_name,
    ao.machine_id,
    m.machine_name,
    ao.status,
    ao.overall_result,
    ao.planned_date,
    ao.actual_start_date,
    ao.actual_end_date,
    ao.total_items,
    ao.passed_items,
    ao.failed_items,
    ao.pass_rate,
    ao.qa_signer_id,
    ao.customer_signer,
    (SELECT COUNT(*) FROM acceptance_issues ai WHERE ai.order_id = ao.id AND ai.status = 'OPEN') as open_issues,
    (SELECT COUNT(*) FROM acceptance_issues ai WHERE ai.order_id = ao.id AND ai.is_blocking = 1 AND ai.status != 'CLOSED') as blocking_issues
FROM acceptance_orders ao
LEFT JOIN projects p ON ao.project_id = p.id
LEFT JOIN machines m ON ao.machine_id = m.id;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================
-- 完成
-- ============================================
