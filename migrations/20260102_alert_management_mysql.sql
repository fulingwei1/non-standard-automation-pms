-- ============================================
-- 预警与异常管理模块 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-02
-- 说明: 预警规则、预警记录、异常事件、处理跟踪等
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. 预警规则表
-- ============================================

CREATE TABLE IF NOT EXISTS `alert_rules` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `rule_code`           VARCHAR(50) NOT NULL COMMENT '规则编码',
    `rule_name`           VARCHAR(200) NOT NULL COMMENT '规则名称',
    `rule_type`           VARCHAR(30) NOT NULL COMMENT '规则类型',

    -- 监控对象
    `target_type`         VARCHAR(30) NOT NULL COMMENT 'PROJECT/MACHINE/PURCHASE/OUTSOURCING/MATERIAL/ACCEPTANCE',
    `target_field`        VARCHAR(100) DEFAULT NULL COMMENT '监控字段',

    -- 触发条件
    `condition_type`      VARCHAR(20) NOT NULL COMMENT 'THRESHOLD/DEVIATION/OVERDUE/CUSTOM',
    `condition_operator`  VARCHAR(10) DEFAULT NULL COMMENT 'GT/LT/EQ/GTE/LTE/BETWEEN',
    `threshold_value`     VARCHAR(100) DEFAULT NULL COMMENT '阈值',
    `threshold_min`       VARCHAR(50) DEFAULT NULL COMMENT '阈值下限',
    `threshold_max`       VARCHAR(50) DEFAULT NULL COMMENT '阈值上限',
    `condition_expr`      TEXT DEFAULT NULL COMMENT '自定义条件表达式',

    -- 预警级别
    `alert_level`         VARCHAR(20) DEFAULT 'WARNING' COMMENT 'INFO/WARNING/CRITICAL/URGENT',

    -- 提前预警
    `advance_days`        INT DEFAULT 0 COMMENT '提前预警天数',

    -- 通知配置
    `notify_channels`     JSON DEFAULT NULL COMMENT '通知渠道',
    `notify_roles`        JSON DEFAULT NULL COMMENT '通知角色',
    `notify_users`        JSON DEFAULT NULL COMMENT '指定通知用户',

    -- 执行配置
    `check_frequency`     VARCHAR(20) DEFAULT 'DAILY' COMMENT 'REALTIME/HOURLY/DAILY/WEEKLY',
    `is_enabled`          TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    `is_system`           TINYINT(1) DEFAULT 0 COMMENT '是否系统预置',

    -- 描述
    `description`         TEXT DEFAULT NULL COMMENT '规则说明',
    `solution_guide`      TEXT DEFAULT NULL COMMENT '处理指南',

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_rule_code` (`rule_code`),
    KEY `idx_rules_type` (`rule_type`),
    KEY `idx_rules_target` (`target_type`),
    KEY `idx_rules_enabled` (`is_enabled`),
    CONSTRAINT `fk_rules_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预警规则表';

-- ============================================
-- 2. 预警记录表
-- ============================================

CREATE TABLE IF NOT EXISTS `alert_records` (
    `id`                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `alert_no`            VARCHAR(50) NOT NULL COMMENT '预警编号',
    `rule_id`             INT UNSIGNED NOT NULL COMMENT '触发的规则ID',

    -- 预警对象
    `target_type`         VARCHAR(30) NOT NULL COMMENT '对象类型',
    `target_id`           INT UNSIGNED NOT NULL COMMENT '对象ID',
    `target_no`           VARCHAR(100) DEFAULT NULL COMMENT '对象编号',
    `target_name`         VARCHAR(200) DEFAULT NULL COMMENT '对象名称',

    -- 关联项目
    `project_id`          INT UNSIGNED DEFAULT NULL COMMENT '关联项目ID',
    `machine_id`          INT UNSIGNED DEFAULT NULL COMMENT '关联设备ID',

    -- 预警信息
    `alert_level`         VARCHAR(20) NOT NULL COMMENT 'INFO/WARNING/CRITICAL/URGENT',
    `alert_title`         VARCHAR(200) NOT NULL COMMENT '预警标题',
    `alert_content`       TEXT NOT NULL COMMENT '预警内容',
    `alert_data`          JSON DEFAULT NULL COMMENT '预警数据',

    -- 触发信息
    `triggered_at`        DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '触发时间',
    `trigger_value`       VARCHAR(100) DEFAULT NULL COMMENT '触发时的值',
    `threshold_value`     VARCHAR(100) DEFAULT NULL COMMENT '阈值',

    -- 状态
    `status`              VARCHAR(20) DEFAULT 'PENDING' COMMENT '状态',

    -- 确认信息
    `acknowledged_by`     INT UNSIGNED DEFAULT NULL COMMENT '确认人',
    `acknowledged_at`     DATETIME DEFAULT NULL COMMENT '确认时间',

    -- 处理信息
    `handler_id`          INT UNSIGNED DEFAULT NULL COMMENT '处理人',
    `handle_start_at`     DATETIME DEFAULT NULL COMMENT '开始处理时间',
    `handle_end_at`       DATETIME DEFAULT NULL COMMENT '处理完成时间',
    `handle_result`       TEXT DEFAULT NULL COMMENT '处理结果',
    `handle_note`         TEXT DEFAULT NULL COMMENT '处理说明',

    -- 是否升级
    `is_escalated`        TINYINT(1) DEFAULT 0 COMMENT '是否升级',
    `escalated_at`        DATETIME DEFAULT NULL COMMENT '升级时间',
    `escalated_to`        INT UNSIGNED DEFAULT NULL COMMENT '升级给谁',

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_alert_no` (`alert_no`),
    KEY `idx_alerts_rule` (`rule_id`),
    KEY `idx_alerts_target` (`target_type`, `target_id`),
    KEY `idx_alerts_project` (`project_id`),
    KEY `idx_alerts_status` (`status`),
    KEY `idx_alerts_level` (`alert_level`),
    KEY `idx_alerts_time` (`triggered_at`),
    CONSTRAINT `fk_alerts_rule` FOREIGN KEY (`rule_id`) REFERENCES `alert_rules` (`id`),
    CONSTRAINT `fk_alerts_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_alerts_machine` FOREIGN KEY (`machine_id`) REFERENCES `machines` (`id`),
    CONSTRAINT `fk_alerts_acknowledged_by` FOREIGN KEY (`acknowledged_by`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_alerts_handler` FOREIGN KEY (`handler_id`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_alerts_escalated_to` FOREIGN KEY (`escalated_to`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预警记录表';

-- ============================================
-- 3. 预警通知记录表
-- ============================================

CREATE TABLE IF NOT EXISTS `alert_notifications` (
    `id`                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `alert_id`            BIGINT UNSIGNED NOT NULL COMMENT '预警记录ID',

    -- 通知信息
    `notify_channel`      VARCHAR(20) NOT NULL COMMENT 'EMAIL/SMS/SYSTEM/WECHAT',
    `notify_target`       VARCHAR(200) NOT NULL COMMENT '通知目标',
    `notify_user_id`      INT UNSIGNED DEFAULT NULL COMMENT '通知用户ID',

    -- 通知内容
    `notify_title`        VARCHAR(200) DEFAULT NULL COMMENT '通知标题',
    `notify_content`      TEXT DEFAULT NULL COMMENT '通知内容',

    -- 状态
    `status`              VARCHAR(20) DEFAULT 'PENDING' COMMENT 'PENDING/SENT/FAILED/READ',
    `sent_at`             DATETIME DEFAULT NULL COMMENT '发送时间',
    `read_at`             DATETIME DEFAULT NULL COMMENT '阅读时间',
    `error_message`       TEXT DEFAULT NULL COMMENT '错误信息',

    -- 重试
    `retry_count`         INT DEFAULT 0 COMMENT '重试次数',
    `next_retry_at`       DATETIME DEFAULT NULL COMMENT '下次重试时间',

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_notifications_alert` (`alert_id`),
    KEY `idx_notifications_user` (`notify_user_id`),
    KEY `idx_notifications_status` (`status`),
    CONSTRAINT `fk_notifications_alert` FOREIGN KEY (`alert_id`) REFERENCES `alert_records` (`id`),
    CONSTRAINT `fk_notifications_user` FOREIGN KEY (`notify_user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预警通知记录表';

-- ============================================
-- 4. 异常事件表
-- ============================================

CREATE TABLE IF NOT EXISTS `exception_events` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `event_no`            VARCHAR(50) NOT NULL COMMENT '异常编号',

    -- 异常来源
    `source_type`         VARCHAR(30) NOT NULL COMMENT 'ALERT/MANUAL/ACCEPTANCE/OUTSOURCING/OTHER',
    `source_id`           INT UNSIGNED DEFAULT NULL COMMENT '来源ID',
    `alert_id`            BIGINT UNSIGNED DEFAULT NULL COMMENT '关联预警ID',

    -- 关联对象
    `project_id`          INT UNSIGNED DEFAULT NULL COMMENT '项目ID',
    `machine_id`          INT UNSIGNED DEFAULT NULL COMMENT '设备ID',

    -- 异常信息
    `event_type`          VARCHAR(30) NOT NULL COMMENT 'SCHEDULE/QUALITY/COST/RESOURCE/SAFETY/OTHER',
    `severity`            VARCHAR(20) NOT NULL COMMENT 'MINOR/MAJOR/CRITICAL/BLOCKER',
    `event_title`         VARCHAR(200) NOT NULL COMMENT '异常标题',
    `event_description`   TEXT NOT NULL COMMENT '异常描述',

    -- 发现信息
    `discovered_at`       DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '发现时间',
    `discovered_by`       INT UNSIGNED DEFAULT NULL COMMENT '发现人',
    `discovery_location`  VARCHAR(200) DEFAULT NULL COMMENT '发现地点',

    -- 影响评估
    `impact_scope`        VARCHAR(20) DEFAULT NULL COMMENT 'LOCAL/MODULE/PROJECT/MULTI_PROJECT',
    `impact_description`  TEXT DEFAULT NULL COMMENT '影响描述',
    `schedule_impact`     INT DEFAULT 0 COMMENT '工期影响(天)',
    `cost_impact`         DECIMAL(14,2) DEFAULT 0 COMMENT '成本影响',

    -- 状态
    `status`              VARCHAR(20) DEFAULT 'OPEN' COMMENT '状态',

    -- 责任人
    `responsible_dept`    VARCHAR(50) DEFAULT NULL COMMENT '责任部门',
    `responsible_user_id` INT UNSIGNED DEFAULT NULL COMMENT '责任人',

    -- 处理期限
    `due_date`            DATE DEFAULT NULL COMMENT '要求完成日期',
    `is_overdue`          TINYINT(1) DEFAULT 0 COMMENT '是否超期',

    -- 根本原因
    `root_cause`          TEXT DEFAULT NULL COMMENT '根本原因分析',
    `cause_category`      VARCHAR(50) DEFAULT NULL COMMENT '原因分类',

    -- 解决方案
    `solution`            TEXT DEFAULT NULL COMMENT '解决方案',
    `preventive_measures` TEXT DEFAULT NULL COMMENT '预防措施',

    -- 处理结果
    `resolved_at`         DATETIME DEFAULT NULL COMMENT '解决时间',
    `resolved_by`         INT UNSIGNED DEFAULT NULL COMMENT '解决人',
    `resolution_note`     TEXT DEFAULT NULL COMMENT '解决说明',

    -- 验证
    `verified_at`         DATETIME DEFAULT NULL COMMENT '验证时间',
    `verified_by`         INT UNSIGNED DEFAULT NULL COMMENT '验证人',
    `verification_result` VARCHAR(20) DEFAULT NULL COMMENT 'VERIFIED/REJECTED',

    -- 附件
    `attachments`         JSON DEFAULT NULL COMMENT '附件',

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_event_no` (`event_no`),
    KEY `idx_events_project` (`project_id`),
    KEY `idx_events_type` (`event_type`),
    KEY `idx_events_severity` (`severity`),
    KEY `idx_events_status` (`status`),
    KEY `idx_events_responsible` (`responsible_user_id`),
    CONSTRAINT `fk_events_alert` FOREIGN KEY (`alert_id`) REFERENCES `alert_records` (`id`),
    CONSTRAINT `fk_events_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_events_machine` FOREIGN KEY (`machine_id`) REFERENCES `machines` (`id`),
    CONSTRAINT `fk_events_discovered_by` FOREIGN KEY (`discovered_by`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_events_responsible` FOREIGN KEY (`responsible_user_id`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_events_resolved_by` FOREIGN KEY (`resolved_by`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_events_verified_by` FOREIGN KEY (`verified_by`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_events_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='异常事件表';

-- ============================================
-- 5. 异常处理记录表
-- ============================================

CREATE TABLE IF NOT EXISTS `exception_actions` (
    `id`                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `event_id`            INT UNSIGNED NOT NULL COMMENT '异常事件ID',

    -- 操作信息
    `action_type`         VARCHAR(30) NOT NULL COMMENT '操作类型',
    `action_content`      TEXT NOT NULL COMMENT '操作内容',

    -- 状态变更
    `old_status`          VARCHAR(20) DEFAULT NULL COMMENT '原状态',
    `new_status`          VARCHAR(20) DEFAULT NULL COMMENT '新状态',

    -- 附件
    `attachments`         JSON DEFAULT NULL COMMENT '附件',

    `created_by`          INT UNSIGNED DEFAULT NULL,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_actions_event` (`event_id`),
    KEY `idx_actions_type` (`action_type`),
    CONSTRAINT `fk_actions_event` FOREIGN KEY (`event_id`) REFERENCES `exception_events` (`id`),
    CONSTRAINT `fk_actions_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='异常处理记录表';

-- ============================================
-- 6. 异常升级记录表
-- ============================================

CREATE TABLE IF NOT EXISTS `exception_escalations` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `event_id`            INT UNSIGNED NOT NULL COMMENT '异常事件ID',
    `escalation_level`    INT NOT NULL COMMENT '升级层级',

    -- 升级信息
    `escalated_from`      INT UNSIGNED DEFAULT NULL COMMENT '升级发起人',
    `escalated_to`        INT UNSIGNED NOT NULL COMMENT '升级接收人',
    `escalated_at`        DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '升级时间',
    `escalation_reason`   TEXT DEFAULT NULL COMMENT '升级原因',

    -- 响应
    `response_status`     VARCHAR(20) DEFAULT 'PENDING' COMMENT 'PENDING/ACCEPTED/DELEGATED',
    `responded_at`        DATETIME DEFAULT NULL COMMENT '响应时间',
    `response_note`       TEXT DEFAULT NULL COMMENT '响应说明',

    PRIMARY KEY (`id`),
    KEY `idx_escalations_event` (`event_id`),
    CONSTRAINT `fk_escalations_event` FOREIGN KEY (`event_id`) REFERENCES `exception_events` (`id`),
    CONSTRAINT `fk_escalations_from` FOREIGN KEY (`escalated_from`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_escalations_to` FOREIGN KEY (`escalated_to`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='异常升级记录表';

-- ============================================
-- 7. 预警统计表
-- ============================================

CREATE TABLE IF NOT EXISTS `alert_statistics` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `stat_date`           DATE NOT NULL COMMENT '统计日期',
    `stat_type`           VARCHAR(20) NOT NULL COMMENT 'DAILY/WEEKLY/MONTHLY',

    -- 预警统计
    `total_alerts`        INT DEFAULT 0 COMMENT '预警总数',
    `info_alerts`         INT DEFAULT 0 COMMENT '提示级别',
    `warning_alerts`      INT DEFAULT 0 COMMENT '警告级别',
    `critical_alerts`     INT DEFAULT 0 COMMENT '严重级别',
    `urgent_alerts`       INT DEFAULT 0 COMMENT '紧急级别',

    -- 处理统计
    `pending_alerts`      INT DEFAULT 0 COMMENT '待处理',
    `processing_alerts`   INT DEFAULT 0 COMMENT '处理中',
    `resolved_alerts`     INT DEFAULT 0 COMMENT '已解决',
    `ignored_alerts`      INT DEFAULT 0 COMMENT '已忽略',

    -- 异常统计
    `total_exceptions`    INT DEFAULT 0 COMMENT '异常总数',
    `open_exceptions`     INT DEFAULT 0 COMMENT '未关闭异常',
    `overdue_exceptions`  INT DEFAULT 0 COMMENT '超期异常',

    -- 响应时间(小时)
    `avg_response_time`   DECIMAL(10,2) DEFAULT 0 COMMENT '平均响应时间',
    `avg_resolve_time`    DECIMAL(10,2) DEFAULT 0 COMMENT '平均解决时间',

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_stat` (`stat_date`, `stat_type`),
    KEY `idx_statistics_date` (`stat_date`),
    KEY `idx_statistics_type` (`stat_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预警统计表';

-- ============================================
-- 8. 项目健康度快照表
-- ============================================

CREATE TABLE IF NOT EXISTS `project_health_snapshots` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `project_id`          INT UNSIGNED NOT NULL COMMENT '项目ID',
    `snapshot_date`       DATE NOT NULL COMMENT '快照日期',

    -- 健康指标
    `overall_health`      VARCHAR(10) NOT NULL COMMENT 'H1/H2/H3/H4',
    `schedule_health`     VARCHAR(10) DEFAULT NULL COMMENT '进度健康度',
    `cost_health`         VARCHAR(10) DEFAULT NULL COMMENT '成本健康度',
    `quality_health`      VARCHAR(10) DEFAULT NULL COMMENT '质量健康度',
    `resource_health`     VARCHAR(10) DEFAULT NULL COMMENT '资源健康度',

    -- 健康评分(0-100)
    `health_score`        INT DEFAULT 0 COMMENT '综合评分',

    -- 风险指标
    `open_alerts`         INT DEFAULT 0 COMMENT '未处理预警数',
    `open_exceptions`     INT DEFAULT 0 COMMENT '未关闭异常数',
    `blocking_issues`     INT DEFAULT 0 COMMENT '阻塞问题数',

    -- 进度指标
    `schedule_variance`   DECIMAL(5,2) DEFAULT 0 COMMENT '进度偏差(%)',
    `milestone_on_track`  INT DEFAULT 0 COMMENT '按期里程碑数',
    `milestone_delayed`   INT DEFAULT 0 COMMENT '延期里程碑数',

    -- 成本指标
    `cost_variance`       DECIMAL(5,2) DEFAULT 0 COMMENT '成本偏差(%)',
    `budget_used_pct`     DECIMAL(5,2) DEFAULT 0 COMMENT '预算使用率(%)',

    -- 主要风险
    `top_risks`           JSON DEFAULT NULL COMMENT '主要风险',

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_health` (`project_id`, `snapshot_date`),
    KEY `idx_health_project` (`project_id`),
    KEY `idx_health_date` (`snapshot_date`),
    CONSTRAINT `fk_health_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目健康度快照表';

-- ============================================
-- 9. 预警规则模板表
-- ============================================

CREATE TABLE IF NOT EXISTS `alert_rule_templates` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `template_code`       VARCHAR(50) NOT NULL COMMENT '模板编码',
    `template_name`       VARCHAR(200) NOT NULL COMMENT '模板名称',
    `template_category`   VARCHAR(30) NOT NULL COMMENT '模板分类',

    -- 规则配置
    `rule_config`         JSON NOT NULL COMMENT '规则配置',

    -- 说明
    `description`         TEXT DEFAULT NULL COMMENT '模板说明',
    `usage_guide`         TEXT DEFAULT NULL COMMENT '使用指南',

    `is_active`           TINYINT(1) DEFAULT 1,
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_template_code` (`template_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预警规则模板表';

-- ============================================
-- 10. 视图定义
-- ============================================

-- 待处理预警视图
CREATE OR REPLACE VIEW `v_pending_alerts` AS
SELECT
    ar.id,
    ar.alert_no,
    ar.alert_level,
    ar.alert_title,
    ar.target_type,
    ar.target_no,
    ar.target_name,
    ar.project_id,
    p.project_name,
    ar.triggered_at,
    ar.status,
    ar.handler_id,
    u.username as handler_name,
    r.rule_name,
    DATEDIFF(NOW(), ar.triggered_at) as pending_days
FROM alert_records ar
LEFT JOIN projects p ON ar.project_id = p.id
LEFT JOIN users u ON ar.handler_id = u.id
LEFT JOIN alert_rules r ON ar.rule_id = r.id
WHERE ar.status IN ('PENDING', 'ACKNOWLEDGED', 'PROCESSING');

-- 未关闭异常视图
CREATE OR REPLACE VIEW `v_open_exceptions` AS
SELECT
    ee.id,
    ee.event_no,
    ee.event_type,
    ee.severity,
    ee.event_title,
    ee.project_id,
    p.project_name,
    ee.machine_id,
    m.machine_name,
    ee.status,
    ee.discovered_at,
    ee.due_date,
    ee.is_overdue,
    ee.responsible_user_id,
    u.username as responsible_name,
    DATEDIFF(NOW(), ee.discovered_at) as open_days
FROM exception_events ee
LEFT JOIN projects p ON ee.project_id = p.id
LEFT JOIN machines m ON ee.machine_id = m.id
LEFT JOIN users u ON ee.responsible_user_id = u.id
WHERE ee.status NOT IN ('CLOSED', 'DEFERRED');

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================
-- 完成
-- ============================================
