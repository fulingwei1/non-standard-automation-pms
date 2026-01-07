-- ============================================
-- 变更管理模块(ECN) - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-02
-- 说明: ECN主表、评估、审批、任务、影响追溯等
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. ECN主表
-- ============================================

CREATE TABLE IF NOT EXISTS `ecn` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `ecn_no`              VARCHAR(50) NOT NULL COMMENT 'ECN编号',
    `ecn_title`           VARCHAR(200) NOT NULL COMMENT 'ECN标题',
    `ecn_type`            VARCHAR(20) NOT NULL COMMENT '变更类型',

    `source_type`         VARCHAR(20) NOT NULL COMMENT '来源类型',
    `source_no`           VARCHAR(100) DEFAULT NULL COMMENT '来源单号',
    `source_id`           INT UNSIGNED DEFAULT NULL COMMENT '来源ID',

    `project_id`          INT UNSIGNED NOT NULL COMMENT '项目ID',
    `machine_id`          INT UNSIGNED DEFAULT NULL COMMENT '设备ID',

    `change_reason`       TEXT NOT NULL COMMENT '变更原因',
    `change_description`  TEXT NOT NULL COMMENT '变更内容描述',
    `change_scope`        VARCHAR(20) DEFAULT 'PARTIAL' COMMENT '变更范围',

    `priority`            VARCHAR(20) DEFAULT 'NORMAL' COMMENT '优先级',
    `urgency`             VARCHAR(20) DEFAULT 'NORMAL' COMMENT '紧急程度',

    `cost_impact`         DECIMAL(14,2) DEFAULT 0 COMMENT '成本影响',
    `schedule_impact_days` INT DEFAULT 0 COMMENT '工期影响',
    `quality_impact`      VARCHAR(20) DEFAULT NULL COMMENT '质量影响',

    `status`              VARCHAR(20) DEFAULT 'DRAFT' COMMENT '状态',
    `current_step`        VARCHAR(50) DEFAULT NULL COMMENT '当前步骤',

    `applicant_id`        INT UNSIGNED DEFAULT NULL COMMENT '申请人',
    `applicant_dept`      VARCHAR(100) DEFAULT NULL COMMENT '申请部门',
    `applied_at`          DATETIME DEFAULT NULL COMMENT '申请时间',

    `approval_result`     VARCHAR(20) DEFAULT NULL COMMENT '审批结果',
    `approval_note`       TEXT DEFAULT NULL COMMENT '审批意见',
    `approved_at`         DATETIME DEFAULT NULL COMMENT '审批时间',

    `execution_start`     DATETIME DEFAULT NULL COMMENT '执行开始',
    `execution_end`       DATETIME DEFAULT NULL COMMENT '执行结束',
    `execution_note`      TEXT DEFAULT NULL COMMENT '执行说明',

    `closed_at`           DATETIME DEFAULT NULL COMMENT '关闭时间',
    `closed_by`           INT UNSIGNED DEFAULT NULL COMMENT '关闭人',

    `attachments`         JSON DEFAULT NULL COMMENT '附件',

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_ecn_no` (`ecn_no`),
    KEY `idx_ecn_project` (`project_id`),
    KEY `idx_ecn_status` (`status`),
    KEY `idx_ecn_type` (`ecn_type`),
    KEY `idx_ecn_applicant` (`applicant_id`),
    CONSTRAINT `fk_ecn_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_ecn_machine` FOREIGN KEY (`machine_id`) REFERENCES `machines` (`id`),
    CONSTRAINT `fk_ecn_applicant` FOREIGN KEY (`applicant_id`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_ecn_closed_by` FOREIGN KEY (`closed_by`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_ecn_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ECN主表';

-- ============================================
-- 2. ECN评估表
-- ============================================

CREATE TABLE IF NOT EXISTS `ecn_evaluations` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `ecn_id`              INT UNSIGNED NOT NULL COMMENT 'ECN ID',
    `eval_dept`           VARCHAR(50) NOT NULL COMMENT '评估部门',

    `evaluator_id`        INT UNSIGNED DEFAULT NULL COMMENT '评估人',
    `evaluator_name`      VARCHAR(50) DEFAULT NULL COMMENT '评估人姓名',

    `impact_analysis`     TEXT DEFAULT NULL COMMENT '影响分析',
    `cost_estimate`       DECIMAL(14,2) DEFAULT 0 COMMENT '成本估算',
    `schedule_estimate`   INT DEFAULT 0 COMMENT '工期估算',
    `resource_requirement` TEXT DEFAULT NULL COMMENT '资源需求',
    `risk_assessment`     TEXT DEFAULT NULL COMMENT '风险评估',

    `eval_result`         VARCHAR(20) DEFAULT NULL COMMENT '评估结论',
    `eval_opinion`        TEXT DEFAULT NULL COMMENT '评估意见',
    `conditions`          TEXT DEFAULT NULL COMMENT '附加条件',

    `status`              VARCHAR(20) DEFAULT 'PENDING' COMMENT '状态',
    `evaluated_at`        DATETIME DEFAULT NULL COMMENT '评估时间',

    `attachments`         JSON DEFAULT NULL,

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_evaluations_ecn` (`ecn_id`),
    KEY `idx_evaluations_dept` (`eval_dept`),
    KEY `idx_evaluations_status` (`status`),
    CONSTRAINT `fk_evaluations_ecn` FOREIGN KEY (`ecn_id`) REFERENCES `ecn` (`id`),
    CONSTRAINT `fk_evaluations_evaluator` FOREIGN KEY (`evaluator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ECN评估表';

-- ============================================
-- 3. ECN审批表
-- ============================================

CREATE TABLE IF NOT EXISTS `ecn_approvals` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `ecn_id`              INT UNSIGNED NOT NULL COMMENT 'ECN ID',
    `approval_level`      INT NOT NULL COMMENT '审批层级',
    `approval_role`       VARCHAR(50) NOT NULL COMMENT '审批角色',

    `approver_id`         INT UNSIGNED DEFAULT NULL COMMENT '审批人ID',
    `approver_name`       VARCHAR(50) DEFAULT NULL COMMENT '审批人姓名',

    `approval_result`     VARCHAR(20) DEFAULT NULL COMMENT '审批结果',
    `approval_opinion`    TEXT DEFAULT NULL COMMENT '审批意见',

    `status`              VARCHAR(20) DEFAULT 'PENDING' COMMENT '状态',
    `approved_at`         DATETIME DEFAULT NULL COMMENT '审批时间',

    `due_date`            DATETIME DEFAULT NULL COMMENT '审批期限',
    `is_overdue`          TINYINT(1) DEFAULT 0 COMMENT '是否超期',

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_approvals_ecn` (`ecn_id`),
    KEY `idx_approvals_approver` (`approver_id`),
    KEY `idx_approvals_status` (`status`),
    CONSTRAINT `fk_approvals_ecn` FOREIGN KEY (`ecn_id`) REFERENCES `ecn` (`id`),
    CONSTRAINT `fk_approvals_approver` FOREIGN KEY (`approver_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ECN审批表';

-- ============================================
-- 4. ECN执行任务表
-- ============================================

CREATE TABLE IF NOT EXISTS `ecn_tasks` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `ecn_id`              INT UNSIGNED NOT NULL COMMENT 'ECN ID',
    `task_no`             INT NOT NULL COMMENT '任务序号',
    `task_name`           VARCHAR(200) NOT NULL COMMENT '任务名称',
    `task_type`           VARCHAR(50) DEFAULT NULL COMMENT '任务类型',
    `task_dept`           VARCHAR(50) DEFAULT NULL COMMENT '责任部门',

    `task_description`    TEXT DEFAULT NULL COMMENT '任务描述',
    `deliverables`        TEXT DEFAULT NULL COMMENT '交付物要求',

    `assignee_id`         INT UNSIGNED DEFAULT NULL COMMENT '负责人',
    `assignee_name`       VARCHAR(50) DEFAULT NULL COMMENT '负责人姓名',

    `planned_start`       DATE DEFAULT NULL COMMENT '计划开始',
    `planned_end`         DATE DEFAULT NULL COMMENT '计划结束',
    `actual_start`        DATE DEFAULT NULL COMMENT '实际开始',
    `actual_end`          DATE DEFAULT NULL COMMENT '实际结束',

    `progress_pct`        INT DEFAULT 0 COMMENT '进度百分比',

    `status`              VARCHAR(20) DEFAULT 'PENDING' COMMENT '状态',

    `completion_note`     TEXT DEFAULT NULL COMMENT '完成说明',
    `attachments`         JSON DEFAULT NULL COMMENT '附件',

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_tasks_ecn` (`ecn_id`),
    KEY `idx_tasks_assignee` (`assignee_id`),
    KEY `idx_tasks_status` (`status`),
    CONSTRAINT `fk_tasks_ecn` FOREIGN KEY (`ecn_id`) REFERENCES `ecn` (`id`),
    CONSTRAINT `fk_tasks_assignee` FOREIGN KEY (`assignee_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ECN执行任务表';

-- ============================================
-- 5. ECN受影响物料表
-- ============================================

CREATE TABLE IF NOT EXISTS `ecn_affected_materials` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `ecn_id`              INT UNSIGNED NOT NULL COMMENT 'ECN ID',
    `material_id`         INT UNSIGNED DEFAULT NULL COMMENT '物料ID',
    `bom_item_id`         INT UNSIGNED DEFAULT NULL COMMENT 'BOM行ID',

    `material_code`       VARCHAR(50) NOT NULL,
    `material_name`       VARCHAR(200) NOT NULL,
    `specification`       VARCHAR(500) DEFAULT NULL,

    `change_type`         VARCHAR(20) NOT NULL COMMENT '变更类型',

    `old_quantity`        DECIMAL(10,4) DEFAULT NULL,
    `old_specification`   VARCHAR(500) DEFAULT NULL,
    `old_supplier_id`     INT UNSIGNED DEFAULT NULL,

    `new_quantity`        DECIMAL(10,4) DEFAULT NULL,
    `new_specification`   VARCHAR(500) DEFAULT NULL,
    `new_supplier_id`     INT UNSIGNED DEFAULT NULL,

    `cost_impact`         DECIMAL(12,2) DEFAULT 0 COMMENT '成本影响',

    `status`              VARCHAR(20) DEFAULT 'PENDING' COMMENT '处理状态',
    `processed_at`        DATETIME DEFAULT NULL,

    `remark`              TEXT DEFAULT NULL,

    PRIMARY KEY (`id`),
    KEY `idx_materials_ecn` (`ecn_id`),
    KEY `idx_materials_material` (`material_id`),
    CONSTRAINT `fk_materials_ecn` FOREIGN KEY (`ecn_id`) REFERENCES `ecn` (`id`),
    CONSTRAINT `fk_materials_material` FOREIGN KEY (`material_id`) REFERENCES `materials` (`id`),
    CONSTRAINT `fk_materials_bom` FOREIGN KEY (`bom_item_id`) REFERENCES `bom_items` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ECN受影响物料表';

-- ============================================
-- 6. ECN受影响订单表
-- ============================================

CREATE TABLE IF NOT EXISTS `ecn_affected_orders` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `ecn_id`              INT UNSIGNED NOT NULL COMMENT 'ECN ID',
    `order_type`          VARCHAR(20) NOT NULL COMMENT '订单类型',
    `order_id`            INT UNSIGNED NOT NULL COMMENT '订单ID',
    `order_no`            VARCHAR(50) NOT NULL COMMENT '订单号',

    `impact_description`  TEXT DEFAULT NULL COMMENT '影响描述',

    `action_type`         VARCHAR(20) DEFAULT NULL COMMENT '处理方式',
    `action_description`  TEXT DEFAULT NULL COMMENT '处理说明',

    `status`              VARCHAR(20) DEFAULT 'PENDING' COMMENT '处理状态',
    `processed_by`        INT UNSIGNED DEFAULT NULL,
    `processed_at`        DATETIME DEFAULT NULL,

    PRIMARY KEY (`id`),
    KEY `idx_orders_ecn` (`ecn_id`),
    CONSTRAINT `fk_orders_ecn` FOREIGN KEY (`ecn_id`) REFERENCES `ecn` (`id`),
    CONSTRAINT `fk_orders_processed_by` FOREIGN KEY (`processed_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ECN受影响订单表';

-- ============================================
-- 7. ECN流转日志表
-- ============================================

CREATE TABLE IF NOT EXISTS `ecn_logs` (
    `id`                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `ecn_id`              INT UNSIGNED NOT NULL COMMENT 'ECN ID',
    `log_type`            VARCHAR(20) NOT NULL COMMENT '日志类型',
    `log_action`          VARCHAR(50) NOT NULL COMMENT '操作动作',

    `old_status`          VARCHAR(20) DEFAULT NULL,
    `new_status`          VARCHAR(20) DEFAULT NULL,

    `log_content`         TEXT DEFAULT NULL COMMENT '日志内容',
    `attachments`         JSON DEFAULT NULL COMMENT '附件',

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_logs_ecn` (`ecn_id`),
    KEY `idx_logs_time` (`created_at`),
    CONSTRAINT `fk_logs_ecn` FOREIGN KEY (`ecn_id`) REFERENCES `ecn` (`id`),
    CONSTRAINT `fk_logs_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ECN流转日志表';

-- ============================================
-- 8. ECN类型配置表
-- ============================================

CREATE TABLE IF NOT EXISTS `ecn_types` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `type_code`           VARCHAR(20) NOT NULL COMMENT '类型编码',
    `type_name`           VARCHAR(50) NOT NULL COMMENT '类型名称',
    `description`         TEXT DEFAULT NULL COMMENT '描述',

    `required_depts`      JSON DEFAULT NULL COMMENT '必需评估部门',
    `optional_depts`      JSON DEFAULT NULL COMMENT '可选评估部门',

    `approval_matrix`     JSON DEFAULT NULL COMMENT '审批矩阵',

    `is_active`           TINYINT(1) DEFAULT 1,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_type_code` (`type_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ECN类型配置表';

-- ============================================
-- 9. ECN审批矩阵配置表
-- ============================================

CREATE TABLE IF NOT EXISTS `ecn_approval_matrix` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `ecn_type`            VARCHAR(20) DEFAULT NULL COMMENT 'ECN类型',
    `condition_type`      VARCHAR(20) NOT NULL COMMENT '条件类型',
    `condition_min`       DECIMAL(14,2) DEFAULT NULL COMMENT '条件下限',
    `condition_max`       DECIMAL(14,2) DEFAULT NULL COMMENT '条件上限',

    `approval_level`      INT NOT NULL COMMENT '审批层级',
    `approval_role`       VARCHAR(50) NOT NULL COMMENT '审批角色',

    `is_active`           TINYINT(1) DEFAULT 1,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_matrix_type` (`ecn_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ECN审批矩阵配置表';

-- ============================================
-- 10. 视图定义
-- ============================================

CREATE OR REPLACE VIEW `v_ecn_overview` AS
SELECT
    e.id,
    e.ecn_no,
    e.ecn_title,
    e.ecn_type,
    e.project_id,
    p.project_name,
    e.status,
    e.priority,
    e.cost_impact,
    e.schedule_impact_days,
    e.applicant_id,
    u.username as applicant_name,
    e.applied_at,
    e.created_at,
    (SELECT COUNT(*) FROM ecn_evaluations ev WHERE ev.ecn_id = e.id AND ev.status = 'COMPLETED') as completed_evals,
    (SELECT COUNT(*) FROM ecn_evaluations ev WHERE ev.ecn_id = e.id) as total_evals,
    (SELECT COUNT(*) FROM ecn_tasks t WHERE t.ecn_id = e.id AND t.status = 'COMPLETED') as completed_tasks,
    (SELECT COUNT(*) FROM ecn_tasks t WHERE t.ecn_id = e.id) as total_tasks
FROM ecn e
LEFT JOIN projects p ON e.project_id = p.id
LEFT JOIN users u ON e.applicant_id = u.id;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================
-- 完成
-- ============================================
