-- ============================================
-- 项目管理模块 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2025-07-12
-- 说明: 项目、设备、阶段、状态、成员等核心表
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. 项目主表
-- ============================================

CREATE TABLE IF NOT EXISTS `projects` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `project_code`        VARCHAR(50) NOT NULL COMMENT '项目编码',
    `project_name`        VARCHAR(200) NOT NULL COMMENT '项目名称',
    `short_name`          VARCHAR(50) DEFAULT NULL COMMENT '项目简称',

    -- 客户信息
    `customer_id`         INT UNSIGNED DEFAULT NULL COMMENT '客户ID',
    `customer_name`       VARCHAR(200) DEFAULT NULL COMMENT '客户名称',
    `customer_contact`    VARCHAR(100) DEFAULT NULL COMMENT '客户联系人',
    `customer_phone`      VARCHAR(50) DEFAULT NULL COMMENT '联系电话',

    -- 合同信息
    `contract_no`         VARCHAR(100) DEFAULT NULL COMMENT '合同编号',
    `contract_amount`     DECIMAL(14,2) DEFAULT NULL COMMENT '合同金额',
    `contract_date`       DATE DEFAULT NULL COMMENT '合同签订日期',

    -- 项目类型与分类
    `project_type`        VARCHAR(50) DEFAULT 'STANDARD' COMMENT '项目类型',
    `product_category`    VARCHAR(50) DEFAULT NULL COMMENT '产品类别',
    `industry`            VARCHAR(50) DEFAULT NULL COMMENT '行业',

    -- 三维状态
    `stage`               VARCHAR(20) DEFAULT 'S1' COMMENT '阶段：S1-S9',
    `status`              VARCHAR(20) DEFAULT 'ST01' COMMENT '状态',
    `health`              VARCHAR(10) DEFAULT 'H1' COMMENT '健康度：H1-H4',

    -- 时间计划
    `planned_start_date`  DATE DEFAULT NULL COMMENT '计划开始日期',
    `planned_end_date`    DATE DEFAULT NULL COMMENT '计划结束日期',
    `actual_start_date`   DATE DEFAULT NULL COMMENT '实际开始日期',
    `actual_end_date`     DATE DEFAULT NULL COMMENT '实际结束日期',

    -- 进度信息
    `progress_pct`        DECIMAL(5,2) DEFAULT 0 COMMENT '整体进度百分比',

    -- 预算与成本
    `budget_amount`       DECIMAL(14,2) DEFAULT NULL COMMENT '预算金额',
    `actual_cost`         DECIMAL(14,2) DEFAULT 0 COMMENT '实际成本',

    -- 项目团队
    `pm_id`               INT UNSIGNED DEFAULT NULL COMMENT '项目经理ID',
    `pm_name`             VARCHAR(50) DEFAULT NULL COMMENT '项目经理姓名',
    `dept_id`             INT UNSIGNED DEFAULT NULL COMMENT '所属部门',

    -- 优先级与标签
    `priority`            VARCHAR(20) DEFAULT 'NORMAL' COMMENT '优先级',
    `tags`                JSON DEFAULT NULL COMMENT '标签',

    -- 描述
    `description`         TEXT DEFAULT NULL COMMENT '项目描述',
    `requirements`        TEXT DEFAULT NULL COMMENT '项目需求摘要',

    -- 附件
    `attachments`         JSON DEFAULT NULL COMMENT '附件列表',

    -- 状态
    `is_active`           TINYINT(1) DEFAULT 1 COMMENT '是否激活',
    `is_archived`         TINYINT(1) DEFAULT 0 COMMENT '是否归档',

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_project_code` (`project_code`),
    KEY `idx_projects_customer` (`customer_id`),
    KEY `idx_projects_pm` (`pm_id`),
    KEY `idx_projects_stage` (`stage`),
    KEY `idx_projects_health` (`health`),
    KEY `idx_projects_active` (`is_active`),
    CONSTRAINT `fk_projects_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`),
    CONSTRAINT `fk_projects_pm` FOREIGN KEY (`pm_id`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_projects_dept` FOREIGN KEY (`dept_id`) REFERENCES `departments` (`id`),
    CONSTRAINT `fk_projects_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目主表';

-- ============================================
-- 2. 设备/机台表
-- ============================================

CREATE TABLE IF NOT EXISTS `machines` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `project_id`          INT UNSIGNED NOT NULL COMMENT '所属项目',
    `machine_code`        VARCHAR(50) NOT NULL COMMENT '设备编码',
    `machine_name`        VARCHAR(200) NOT NULL COMMENT '设备名称',
    `machine_no`          INT DEFAULT 1 COMMENT '设备序号',

    -- 设备类型
    `machine_type`        VARCHAR(50) DEFAULT NULL COMMENT '设备类型',
    `specification`       TEXT DEFAULT NULL COMMENT '规格描述',

    -- 状态
    `stage`               VARCHAR(20) DEFAULT 'S1' COMMENT '设备阶段',
    `status`              VARCHAR(20) DEFAULT 'ST01' COMMENT '设备状态',
    `health`              VARCHAR(10) DEFAULT 'H1' COMMENT '健康度',

    -- 进度
    `progress_pct`        DECIMAL(5,2) DEFAULT 0 COMMENT '设备进度',

    -- 时间
    `planned_start_date`  DATE DEFAULT NULL COMMENT '计划开始',
    `planned_end_date`    DATE DEFAULT NULL COMMENT '计划结束',
    `actual_start_date`   DATE DEFAULT NULL COMMENT '实际开始',
    `actual_end_date`     DATE DEFAULT NULL COMMENT '实际结束',

    -- FAT/SAT信息
    `fat_date`            DATE DEFAULT NULL COMMENT 'FAT日期',
    `fat_result`          VARCHAR(20) DEFAULT NULL COMMENT 'FAT结果',
    `sat_date`            DATE DEFAULT NULL COMMENT 'SAT日期',
    `sat_result`          VARCHAR(20) DEFAULT NULL COMMENT 'SAT结果',

    -- 发货信息
    `ship_date`           DATE DEFAULT NULL COMMENT '发货日期',
    `ship_address`        VARCHAR(500) DEFAULT NULL COMMENT '发货地址',
    `tracking_no`         VARCHAR(100) DEFAULT NULL COMMENT '物流单号',

    -- 备注
    `remark`              TEXT DEFAULT NULL,

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_machine_project_code` (`project_id`, `machine_code`),
    KEY `idx_machines_stage` (`stage`),
    CONSTRAINT `fk_machines_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备/机台表';

-- ============================================
-- 3. 项目阶段定义表
-- ============================================

CREATE TABLE IF NOT EXISTS `project_stages` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `stage_code`          VARCHAR(20) NOT NULL COMMENT '阶段编码',
    `stage_name`          VARCHAR(50) NOT NULL COMMENT '阶段名称',
    `stage_order`         INT NOT NULL COMMENT '阶段顺序',
    `description`         TEXT DEFAULT NULL COMMENT '阶段描述',

    -- 门控条件
    `gate_conditions`     JSON DEFAULT NULL COMMENT '进入条件',
    `required_deliverables` JSON DEFAULT NULL COMMENT '必需交付物',

    -- 默认时长
    `default_duration_days` INT DEFAULT NULL COMMENT '默认工期',

    -- 显示配置
    `color`               VARCHAR(20) DEFAULT NULL COMMENT '显示颜色',
    `icon`                VARCHAR(50) DEFAULT NULL COMMENT '图标',

    `is_active`           TINYINT(1) DEFAULT 1,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_stage_code` (`stage_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目阶段定义表';

-- ============================================
-- 4. 项目状态定义表
-- ============================================

CREATE TABLE IF NOT EXISTS `project_statuses` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `stage_code`          VARCHAR(20) NOT NULL COMMENT '所属阶段',
    `status_code`         VARCHAR(20) NOT NULL COMMENT '状态编码',
    `status_name`         VARCHAR(50) NOT NULL COMMENT '状态名称',
    `status_order`        INT NOT NULL COMMENT '状态顺序',
    `description`         TEXT DEFAULT NULL COMMENT '状态描述',

    -- 状态类型
    `status_type`         VARCHAR(20) DEFAULT 'NORMAL' COMMENT '状态类型',

    -- 自动流转
    `auto_next_status`    VARCHAR(20) DEFAULT NULL COMMENT '自动下一状态',

    `is_active`           TINYINT(1) DEFAULT 1,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_status_code` (`status_code`),
    KEY `idx_statuses_stage` (`stage_code`),
    CONSTRAINT `fk_statuses_stage` FOREIGN KEY (`stage_code`) REFERENCES `project_stages` (`stage_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目状态定义表';

-- ============================================
-- 5. 项目状态变更日志
-- ============================================

CREATE TABLE IF NOT EXISTS `project_status_logs` (
    `id`                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `project_id`          INT UNSIGNED NOT NULL COMMENT '项目ID',
    `machine_id`          INT UNSIGNED DEFAULT NULL COMMENT '设备ID',

    -- 变更前状态
    `old_stage`           VARCHAR(20) DEFAULT NULL,
    `old_status`          VARCHAR(20) DEFAULT NULL,
    `old_health`          VARCHAR(10) DEFAULT NULL,

    -- 变更后状态
    `new_stage`           VARCHAR(20) DEFAULT NULL,
    `new_status`          VARCHAR(20) DEFAULT NULL,
    `new_health`          VARCHAR(10) DEFAULT NULL,

    -- 变更信息
    `change_type`         VARCHAR(20) NOT NULL COMMENT '变更类型',
    `change_reason`       TEXT DEFAULT NULL COMMENT '变更原因',
    `change_note`         TEXT DEFAULT NULL COMMENT '变更备注',

    -- 操作信息
    `changed_by`          INT UNSIGNED DEFAULT NULL,
    `changed_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_status_logs_project` (`project_id`),
    KEY `idx_status_logs_machine` (`machine_id`),
    KEY `idx_status_logs_time` (`changed_at`),
    CONSTRAINT `fk_status_logs_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_status_logs_machine` FOREIGN KEY (`machine_id`) REFERENCES `machines` (`id`),
    CONSTRAINT `fk_status_logs_changed_by` FOREIGN KEY (`changed_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目状态变更日志';

-- ============================================
-- 6. 项目成员表
-- ============================================

CREATE TABLE IF NOT EXISTS `project_members` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `project_id`          INT UNSIGNED NOT NULL COMMENT '项目ID',
    `user_id`             INT UNSIGNED NOT NULL COMMENT '用户ID',
    `role_code`           VARCHAR(50) NOT NULL COMMENT '角色编码',

    -- 分配信息
    `allocation_pct`      DECIMAL(5,2) DEFAULT 100 COMMENT '分配比例',
    `start_date`          DATE DEFAULT NULL COMMENT '开始日期',
    `end_date`            DATE DEFAULT NULL COMMENT '结束日期',

    -- 状态
    `is_active`           TINYINT(1) DEFAULT 1,

    -- 备注
    `remark`              TEXT DEFAULT NULL,

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_project_member` (`project_id`, `user_id`, `role_code`),
    KEY `idx_members_user` (`user_id`),
    CONSTRAINT `fk_members_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_members_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_members_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目成员表';

-- ============================================
-- 7. 项目里程碑表
-- ============================================

CREATE TABLE IF NOT EXISTS `project_milestones` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `project_id`          INT UNSIGNED NOT NULL COMMENT '项目ID',
    `machine_id`          INT UNSIGNED DEFAULT NULL COMMENT '设备ID',

    `milestone_code`      VARCHAR(50) NOT NULL COMMENT '里程碑编码',
    `milestone_name`      VARCHAR(200) NOT NULL COMMENT '里程碑名称',
    `milestone_type`      VARCHAR(20) DEFAULT 'CUSTOM' COMMENT '里程碑类型',

    -- 时间
    `planned_date`        DATE NOT NULL COMMENT '计划日期',
    `actual_date`         DATE DEFAULT NULL COMMENT '实际完成日期',

    -- 状态
    `status`              VARCHAR(20) DEFAULT 'PENDING' COMMENT '状态',

    -- 关联阶段
    `stage_code`          VARCHAR(20) DEFAULT NULL COMMENT '关联阶段',

    -- 交付物
    `deliverables`        JSON DEFAULT NULL COMMENT '交付物',

    -- 责任人
    `owner_id`            INT UNSIGNED DEFAULT NULL,

    -- 备注
    `description`         TEXT DEFAULT NULL,
    `completion_note`     TEXT DEFAULT NULL,

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_milestones_project` (`project_id`),
    KEY `idx_milestones_status` (`status`),
    KEY `idx_milestones_date` (`planned_date`),
    CONSTRAINT `fk_milestones_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_milestones_machine` FOREIGN KEY (`machine_id`) REFERENCES `machines` (`id`),
    CONSTRAINT `fk_milestones_owner` FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目里程碑表';

-- ============================================
-- 8. 项目回款计划表
-- ============================================

CREATE TABLE IF NOT EXISTS `project_payment_plans` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `project_id`          INT UNSIGNED NOT NULL COMMENT '项目ID',

    `payment_no`          INT NOT NULL COMMENT '期次',
    `payment_name`        VARCHAR(100) NOT NULL COMMENT '款项名称',
    `payment_type`        VARCHAR(20) NOT NULL COMMENT '款项类型',

    -- 金额
    `payment_ratio`       DECIMAL(5,2) DEFAULT NULL COMMENT '比例',
    `planned_amount`      DECIMAL(14,2) NOT NULL COMMENT '计划金额',
    `actual_amount`       DECIMAL(14,2) DEFAULT 0 COMMENT '实际收款',

    -- 时间
    `planned_date`        DATE DEFAULT NULL COMMENT '计划收款日期',
    `actual_date`         DATE DEFAULT NULL COMMENT '实际收款日期',

    -- 触发条件
    `trigger_milestone`   VARCHAR(50) DEFAULT NULL COMMENT '触发里程碑',
    `trigger_condition`   TEXT DEFAULT NULL COMMENT '触发条件描述',

    -- 状态
    `status`              VARCHAR(20) DEFAULT 'PENDING' COMMENT '状态',

    -- 发票信息
    `invoice_no`          VARCHAR(100) DEFAULT NULL COMMENT '发票号',
    `invoice_date`        DATE DEFAULT NULL COMMENT '开票日期',
    `invoice_amount`      DECIMAL(14,2) DEFAULT NULL COMMENT '开票金额',

    `remark`              TEXT DEFAULT NULL,

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_payment_plans_project` (`project_id`),
    KEY `idx_payment_plans_status` (`status`),
    CONSTRAINT `fk_payment_plans_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目回款计划表';

-- ============================================
-- 9. 项目成本记录表
-- ============================================

CREATE TABLE IF NOT EXISTS `project_costs` (
    `id`                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `project_id`          INT UNSIGNED NOT NULL COMMENT '项目ID',
    `machine_id`          INT UNSIGNED DEFAULT NULL COMMENT '设备ID',

    `cost_type`           VARCHAR(50) NOT NULL COMMENT '成本类型',
    `cost_category`       VARCHAR(50) NOT NULL COMMENT '成本分类',

    -- 来源
    `source_module`       VARCHAR(50) DEFAULT NULL COMMENT '来源模块',
    `source_type`         VARCHAR(50) DEFAULT NULL COMMENT '来源类型',
    `source_id`           INT UNSIGNED DEFAULT NULL COMMENT '来源ID',
    `source_no`           VARCHAR(100) DEFAULT NULL COMMENT '来源单号',

    -- 金额
    `amount`              DECIMAL(14,2) NOT NULL COMMENT '金额',
    `tax_amount`          DECIMAL(12,2) DEFAULT 0 COMMENT '税额',

    -- 描述
    `description`         TEXT DEFAULT NULL COMMENT '描述',

    -- 时间
    `cost_date`           DATE NOT NULL COMMENT '成本日期',

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_costs_project` (`project_id`),
    KEY `idx_costs_type` (`cost_type`),
    KEY `idx_costs_date` (`cost_date`),
    CONSTRAINT `fk_costs_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_costs_machine` FOREIGN KEY (`machine_id`) REFERENCES `machines` (`id`),
    CONSTRAINT `fk_costs_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目成本记录表';

-- ============================================
-- 10. 项目文档表
-- ============================================

CREATE TABLE IF NOT EXISTS `project_documents` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `project_id`          INT UNSIGNED NOT NULL COMMENT '项目ID',
    `machine_id`          INT UNSIGNED DEFAULT NULL COMMENT '设备ID',

    `doc_type`            VARCHAR(50) NOT NULL COMMENT '文档类型',
    `doc_category`        VARCHAR(50) DEFAULT NULL COMMENT '文档分类',
    `doc_name`            VARCHAR(200) NOT NULL COMMENT '文档名称',
    `doc_no`              VARCHAR(100) DEFAULT NULL COMMENT '文档编号',
    `version`             VARCHAR(20) DEFAULT '1.0' COMMENT '版本号',

    -- 文件信息
    `file_path`           VARCHAR(500) NOT NULL COMMENT '文件路径',
    `file_name`           VARCHAR(200) NOT NULL COMMENT '原始文件名',
    `file_size`           INT DEFAULT NULL COMMENT '文件大小',
    `file_type`           VARCHAR(50) DEFAULT NULL COMMENT '文件类型',

    -- 状态
    `status`              VARCHAR(20) DEFAULT 'DRAFT' COMMENT '状态',

    -- 审批
    `approved_by`         INT UNSIGNED DEFAULT NULL,
    `approved_at`         DATETIME DEFAULT NULL,

    -- 描述
    `description`         TEXT DEFAULT NULL,

    `uploaded_by`         INT UNSIGNED DEFAULT NULL,
    `uploaded_at`         DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_documents_project` (`project_id`),
    KEY `idx_documents_type` (`doc_type`),
    CONSTRAINT `fk_documents_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_documents_machine` FOREIGN KEY (`machine_id`) REFERENCES `machines` (`id`),
    CONSTRAINT `fk_documents_uploaded_by` FOREIGN KEY (`uploaded_by`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_documents_approved_by` FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目文档表';

-- ============================================
-- 11. 客户表
-- ============================================

CREATE TABLE IF NOT EXISTS `customers` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `customer_code`       VARCHAR(50) NOT NULL COMMENT '客户编码',
    `customer_name`       VARCHAR(200) NOT NULL COMMENT '客户名称',
    `short_name`          VARCHAR(50) DEFAULT NULL COMMENT '简称',

    -- 基本信息
    `customer_type`       VARCHAR(20) DEFAULT 'ENTERPRISE' COMMENT '客户类型',
    `industry`            VARCHAR(50) DEFAULT NULL COMMENT '行业',
    `scale`               VARCHAR(20) DEFAULT NULL COMMENT '规模',

    -- 联系信息
    `contact_person`      VARCHAR(50) DEFAULT NULL COMMENT '联系人',
    `contact_phone`       VARCHAR(50) DEFAULT NULL COMMENT '联系电话',
    `contact_email`       VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    `address`             VARCHAR(500) DEFAULT NULL COMMENT '地址',

    -- 公司信息
    `legal_person`        VARCHAR(50) DEFAULT NULL COMMENT '法人',
    `tax_no`              VARCHAR(50) DEFAULT NULL COMMENT '税号',
    `bank_name`           VARCHAR(100) DEFAULT NULL COMMENT '开户银行',
    `bank_account`        VARCHAR(50) DEFAULT NULL COMMENT '银行账号',

    -- 信用信息
    `credit_level`        VARCHAR(20) DEFAULT NULL COMMENT '信用等级',
    `credit_limit`        DECIMAL(14,2) DEFAULT NULL COMMENT '信用额度',
    `payment_terms`       VARCHAR(50) DEFAULT NULL COMMENT '付款条款',

    -- 客户门户
    `portal_enabled`      TINYINT(1) DEFAULT 0 COMMENT '是否启用门户',
    `portal_username`     VARCHAR(100) DEFAULT NULL COMMENT '门户账号',

    -- 状态
    `status`              VARCHAR(20) DEFAULT 'ACTIVE' COMMENT '状态',

    -- 备注
    `remark`              TEXT DEFAULT NULL,

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_customer_code` (`customer_code`),
    KEY `idx_customers_name` (`customer_name`),
    KEY `idx_customers_industry` (`industry`),
    CONSTRAINT `fk_customers_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户表';

-- ============================================
-- 12. 视图定义
-- ============================================

-- 项目概览视图
CREATE OR REPLACE VIEW `v_project_overview` AS
SELECT
    p.id,
    p.project_code,
    p.project_name,
    p.customer_name,
    p.contract_amount,
    p.stage,
    ps.stage_name,
    p.status,
    pst.status_name,
    p.health,
    p.progress_pct,
    p.planned_start_date,
    p.planned_end_date,
    p.actual_start_date,
    p.pm_name,
    p.priority,
    p.budget_amount,
    p.actual_cost,
    (SELECT COUNT(*) FROM machines m WHERE m.project_id = p.id) as machine_count,
    (SELECT COUNT(*) FROM project_members pm WHERE pm.project_id = p.id AND pm.is_active = 1) as member_count
FROM projects p
LEFT JOIN project_stages ps ON p.stage = ps.stage_code
LEFT JOIN project_statuses pst ON p.status = pst.status_code
WHERE p.is_active = 1;

-- 项目进度统计视图
CREATE OR REPLACE VIEW `v_project_progress` AS
SELECT
    p.id as project_id,
    p.project_code,
    p.project_name,
    p.stage,
    p.progress_pct as overall_progress,
    (SELECT AVG(m.progress_pct) FROM machines m WHERE m.project_id = p.id) as avg_machine_progress,
    (SELECT COUNT(*) FROM machines m WHERE m.project_id = p.id AND m.stage = 'S8') as completed_machines,
    (SELECT COUNT(*) FROM machines m WHERE m.project_id = p.id) as total_machines,
    p.planned_end_date,
    p.actual_end_date,
    DATEDIFF(IFNULL(p.actual_end_date, CURDATE()), p.planned_end_date) as delay_days
FROM projects p
WHERE p.is_active = 1;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================
-- 完成
-- ============================================
