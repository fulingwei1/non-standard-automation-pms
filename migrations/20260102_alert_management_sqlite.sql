-- ============================================
-- 预警与异常管理模块 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-02
-- 说明: 预警规则、预警记录、异常事件、处理跟踪等
-- ============================================

-- ============================================
-- 1. 预警规则表
-- ============================================

CREATE TABLE IF NOT EXISTS alert_rules (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_code           VARCHAR(50) NOT NULL UNIQUE,          -- 规则编码
    rule_name           VARCHAR(200) NOT NULL,                -- 规则名称
    rule_type           VARCHAR(30) NOT NULL,                 -- 规则类型

    -- 监控对象
    target_type         VARCHAR(30) NOT NULL,                 -- PROJECT/MACHINE/PURCHASE/OUTSOURCING/MATERIAL/ACCEPTANCE
    target_field        VARCHAR(100),                         -- 监控字段

    -- 触发条件
    condition_type      VARCHAR(20) NOT NULL,                 -- THRESHOLD/DEVIATION/OVERDUE/CUSTOM
    condition_operator  VARCHAR(10),                          -- GT/LT/EQ/GTE/LTE/BETWEEN
    threshold_value     VARCHAR(100),                         -- 阈值
    threshold_min       VARCHAR(50),                          -- 阈值下限
    threshold_max       VARCHAR(50),                          -- 阈值上限
    condition_expr      TEXT,                                 -- 自定义条件表达式

    -- 预警级别
    alert_level         VARCHAR(20) DEFAULT 'WARNING',        -- INFO/WARNING/CRITICAL/URGENT

    -- 提前预警
    advance_days        INTEGER DEFAULT 0,                    -- 提前预警天数

    -- 通知配置
    notify_channels     TEXT,                                 -- 通知渠道JSON: ["EMAIL","SMS","SYSTEM"]
    notify_roles        TEXT,                                 -- 通知角色JSON
    notify_users        TEXT,                                 -- 指定通知用户JSON

    -- 执行配置
    check_frequency     VARCHAR(20) DEFAULT 'DAILY',          -- REALTIME/HOURLY/DAILY/WEEKLY
    is_enabled          BOOLEAN DEFAULT 1,                    -- 是否启用
    is_system           BOOLEAN DEFAULT 0,                    -- 是否系统预置

    -- 描述
    description         TEXT,                                 -- 规则说明
    solution_guide      TEXT,                                 -- 处理指南

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_alert_rules_type ON alert_rules(rule_type);
CREATE INDEX idx_alert_rules_target ON alert_rules(target_type);
CREATE INDEX idx_alert_rules_enabled ON alert_rules(is_enabled);

-- ============================================
-- 2. 预警记录表
-- ============================================

CREATE TABLE IF NOT EXISTS alert_records (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_no            VARCHAR(50) NOT NULL UNIQUE,          -- 预警编号
    rule_id             INTEGER NOT NULL,                     -- 触发的规则ID

    -- 预警对象
    target_type         VARCHAR(30) NOT NULL,                 -- 对象类型
    target_id           INTEGER NOT NULL,                     -- 对象ID
    target_no           VARCHAR(100),                         -- 对象编号
    target_name         VARCHAR(200),                         -- 对象名称

    -- 关联项目
    project_id          INTEGER,                              -- 关联项目ID
    machine_id          INTEGER,                              -- 关联设备ID

    -- 预警信息
    alert_level         VARCHAR(20) NOT NULL,                 -- INFO/WARNING/CRITICAL/URGENT
    alert_title         VARCHAR(200) NOT NULL,                -- 预警标题
    alert_content       TEXT NOT NULL,                        -- 预警内容
    alert_data          TEXT,                                 -- 预警数据JSON

    -- 触发信息
    triggered_at        DATETIME DEFAULT CURRENT_TIMESTAMP,   -- 触发时间
    trigger_value       VARCHAR(100),                         -- 触发时的值
    threshold_value     VARCHAR(100),                         -- 阈值

    -- 状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/ACKNOWLEDGED/PROCESSING/RESOLVED/IGNORED/EXPIRED

    -- 确认信息
    acknowledged_by     INTEGER,                              -- 确认人
    acknowledged_at     DATETIME,                             -- 确认时间

    -- 处理信息
    handler_id          INTEGER,                              -- 处理人
    handle_start_at     DATETIME,                             -- 开始处理时间
    handle_end_at       DATETIME,                             -- 处理完成时间
    handle_result       TEXT,                                 -- 处理结果
    handle_note         TEXT,                                 -- 处理说明

    -- 是否升级
    is_escalated        BOOLEAN DEFAULT 0,                    -- 是否升级
    escalated_at        DATETIME,                             -- 升级时间
    escalated_to        INTEGER,                              -- 升级给谁

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (rule_id) REFERENCES alert_rules(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (acknowledged_by) REFERENCES users(id),
    FOREIGN KEY (handler_id) REFERENCES users(id),
    FOREIGN KEY (escalated_to) REFERENCES users(id)
);

CREATE INDEX idx_alerts_rule ON alert_records(rule_id);
CREATE INDEX idx_alerts_target ON alert_records(target_type, target_id);
CREATE INDEX idx_alerts_project ON alert_records(project_id);
CREATE INDEX idx_alerts_status ON alert_records(status);
CREATE INDEX idx_alerts_level ON alert_records(alert_level);
CREATE INDEX idx_alerts_time ON alert_records(triggered_at);

-- ============================================
-- 3. 预警通知记录表
-- ============================================

CREATE TABLE IF NOT EXISTS alert_notifications (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id            INTEGER NOT NULL,                     -- 预警记录ID

    -- 通知信息
    notify_channel      VARCHAR(20) NOT NULL,                 -- EMAIL/SMS/SYSTEM/WECHAT
    notify_target       VARCHAR(200) NOT NULL,                -- 通知目标(邮箱/手机/用户ID)
    notify_user_id      INTEGER,                              -- 通知用户ID

    -- 通知内容
    notify_title        VARCHAR(200),                         -- 通知标题
    notify_content      TEXT,                                 -- 通知内容

    -- 状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/SENT/FAILED/READ
    sent_at             DATETIME,                             -- 发送时间
    read_at             DATETIME,                             -- 阅读时间
    error_message       TEXT,                                 -- 错误信息

    -- 重试
    retry_count         INTEGER DEFAULT 0,                    -- 重试次数
    next_retry_at       DATETIME,                             -- 下次重试时间

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (alert_id) REFERENCES alert_records(id),
    FOREIGN KEY (notify_user_id) REFERENCES users(id)
);

CREATE INDEX idx_notifications_alert ON alert_notifications(alert_id);
CREATE INDEX idx_notifications_user ON alert_notifications(notify_user_id);
CREATE INDEX idx_notifications_status ON alert_notifications(status);

-- ============================================
-- 4. 异常事件表
-- ============================================

CREATE TABLE IF NOT EXISTS exception_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    event_no            VARCHAR(50) NOT NULL UNIQUE,          -- 异常编号

    -- 异常来源
    source_type         VARCHAR(30) NOT NULL,                 -- ALERT/MANUAL/ACCEPTANCE/OUTSOURCING/OTHER
    source_id           INTEGER,                              -- 来源ID
    alert_id            INTEGER,                              -- 关联预警ID

    -- 关联对象
    project_id          INTEGER,                              -- 项目ID
    machine_id          INTEGER,                              -- 设备ID

    -- 异常信息
    event_type          VARCHAR(30) NOT NULL,                 -- SCHEDULE/QUALITY/COST/RESOURCE/SAFETY/OTHER
    severity            VARCHAR(20) NOT NULL,                 -- MINOR/MAJOR/CRITICAL/BLOCKER
    event_title         VARCHAR(200) NOT NULL,                -- 异常标题
    event_description   TEXT NOT NULL,                        -- 异常描述

    -- 发现信息
    discovered_at       DATETIME DEFAULT CURRENT_TIMESTAMP,   -- 发现时间
    discovered_by       INTEGER,                              -- 发现人
    discovery_location  VARCHAR(200),                         -- 发现地点

    -- 影响评估
    impact_scope        VARCHAR(20),                          -- LOCAL/MODULE/PROJECT/MULTI_PROJECT
    impact_description  TEXT,                                 -- 影响描述
    schedule_impact     INTEGER DEFAULT 0,                    -- 工期影响(天)
    cost_impact         DECIMAL(14,2) DEFAULT 0,              -- 成本影响

    -- 状态
    status              VARCHAR(20) DEFAULT 'OPEN',           -- OPEN/ANALYZING/RESOLVING/RESOLVED/CLOSED/DEFERRED

    -- 责任人
    responsible_dept    VARCHAR(50),                          -- 责任部门
    responsible_user_id INTEGER,                              -- 责任人

    -- 处理期限
    due_date            DATE,                                 -- 要求完成日期
    is_overdue          BOOLEAN DEFAULT 0,                    -- 是否超期

    -- 根本原因
    root_cause          TEXT,                                 -- 根本原因分析
    cause_category      VARCHAR(50),                          -- 原因分类

    -- 解决方案
    solution            TEXT,                                 -- 解决方案
    preventive_measures TEXT,                                 -- 预防措施

    -- 处理结果
    resolved_at         DATETIME,                             -- 解决时间
    resolved_by         INTEGER,                              -- 解决人
    resolution_note     TEXT,                                 -- 解决说明

    -- 验证
    verified_at         DATETIME,                             -- 验证时间
    verified_by         INTEGER,                              -- 验证人
    verification_result VARCHAR(20),                          -- VERIFIED/REJECTED

    -- 附件
    attachments         TEXT,                                 -- 附件JSON

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (alert_id) REFERENCES alert_records(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (discovered_by) REFERENCES users(id),
    FOREIGN KEY (responsible_user_id) REFERENCES users(id),
    FOREIGN KEY (resolved_by) REFERENCES users(id),
    FOREIGN KEY (verified_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_events_project ON exception_events(project_id);
CREATE INDEX idx_events_type ON exception_events(event_type);
CREATE INDEX idx_events_severity ON exception_events(severity);
CREATE INDEX idx_events_status ON exception_events(status);
CREATE INDEX idx_events_responsible ON exception_events(responsible_user_id);

-- ============================================
-- 5. 异常处理记录表
-- ============================================

CREATE TABLE IF NOT EXISTS exception_actions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id            INTEGER NOT NULL,                     -- 异常事件ID

    -- 操作信息
    action_type         VARCHAR(30) NOT NULL,                 -- COMMENT/STATUS_CHANGE/ASSIGN/ANALYZE/RESOLVE/VERIFY/ESCALATE
    action_content      TEXT NOT NULL,                        -- 操作内容

    -- 状态变更
    old_status          VARCHAR(20),                          -- 原状态
    new_status          VARCHAR(20),                          -- 新状态

    -- 附件
    attachments         TEXT,                                 -- 附件JSON

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (event_id) REFERENCES exception_events(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_actions_event ON exception_actions(event_id);
CREATE INDEX idx_actions_type ON exception_actions(action_type);

-- ============================================
-- 6. 异常升级记录表
-- ============================================

CREATE TABLE IF NOT EXISTS exception_escalations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id            INTEGER NOT NULL,                     -- 异常事件ID
    escalation_level    INTEGER NOT NULL,                     -- 升级层级

    -- 升级信息
    escalated_from      INTEGER,                              -- 升级发起人
    escalated_to        INTEGER NOT NULL,                     -- 升级接收人
    escalated_at        DATETIME DEFAULT CURRENT_TIMESTAMP,   -- 升级时间
    escalation_reason   TEXT,                                 -- 升级原因

    -- 响应
    response_status     VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/ACCEPTED/DELEGATED
    responded_at        DATETIME,                             -- 响应时间
    response_note       TEXT,                                 -- 响应说明

    FOREIGN KEY (event_id) REFERENCES exception_events(id),
    FOREIGN KEY (escalated_from) REFERENCES users(id),
    FOREIGN KEY (escalated_to) REFERENCES users(id)
);

CREATE INDEX idx_escalations_event ON exception_escalations(event_id);

-- ============================================
-- 7. 预警统计表(用于仪表盘)
-- ============================================

CREATE TABLE IF NOT EXISTS alert_statistics (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date           DATE NOT NULL,                        -- 统计日期
    stat_type           VARCHAR(20) NOT NULL,                 -- DAILY/WEEKLY/MONTHLY

    -- 预警统计
    total_alerts        INTEGER DEFAULT 0,                    -- 预警总数
    info_alerts         INTEGER DEFAULT 0,                    -- 提示级别
    warning_alerts      INTEGER DEFAULT 0,                    -- 警告级别
    critical_alerts     INTEGER DEFAULT 0,                    -- 严重级别
    urgent_alerts       INTEGER DEFAULT 0,                    -- 紧急级别

    -- 处理统计
    pending_alerts      INTEGER DEFAULT 0,                    -- 待处理
    processing_alerts   INTEGER DEFAULT 0,                    -- 处理中
    resolved_alerts     INTEGER DEFAULT 0,                    -- 已解决
    ignored_alerts      INTEGER DEFAULT 0,                    -- 已忽略

    -- 异常统计
    total_exceptions    INTEGER DEFAULT 0,                    -- 异常总数
    open_exceptions     INTEGER DEFAULT 0,                    -- 未关闭异常
    overdue_exceptions  INTEGER DEFAULT 0,                    -- 超期异常

    -- 响应时间(小时)
    avg_response_time   DECIMAL(10,2) DEFAULT 0,              -- 平均响应时间
    avg_resolve_time    DECIMAL(10,2) DEFAULT 0,              -- 平均解决时间

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(stat_date, stat_type)
);

CREATE INDEX idx_statistics_date ON alert_statistics(stat_date);
CREATE INDEX idx_statistics_type ON alert_statistics(stat_type);

-- ============================================
-- 8. 项目健康度快照表
-- ============================================

CREATE TABLE IF NOT EXISTS project_health_snapshots (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID
    snapshot_date       DATE NOT NULL,                        -- 快照日期

    -- 健康指标
    overall_health      VARCHAR(10) NOT NULL,                 -- H1/H2/H3/H4
    schedule_health     VARCHAR(10),                          -- 进度健康度
    cost_health         VARCHAR(10),                          -- 成本健康度
    quality_health      VARCHAR(10),                          -- 质量健康度
    resource_health     VARCHAR(10),                          -- 资源健康度

    -- 健康评分(0-100)
    health_score        INTEGER DEFAULT 0,                    -- 综合评分

    -- 风险指标
    open_alerts         INTEGER DEFAULT 0,                    -- 未处理预警数
    open_exceptions     INTEGER DEFAULT 0,                    -- 未关闭异常数
    blocking_issues     INTEGER DEFAULT 0,                    -- 阻塞问题数

    -- 进度指标
    schedule_variance   DECIMAL(5,2) DEFAULT 0,               -- 进度偏差(%)
    milestone_on_track  INTEGER DEFAULT 0,                    -- 按期里程碑数
    milestone_delayed   INTEGER DEFAULT 0,                    -- 延期里程碑数

    -- 成本指标
    cost_variance       DECIMAL(5,2) DEFAULT 0,               -- 成本偏差(%)
    budget_used_pct     DECIMAL(5,2) DEFAULT 0,               -- 预算使用率(%)

    -- 主要风险
    top_risks           TEXT,                                 -- 主要风险JSON

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    UNIQUE(project_id, snapshot_date)
);

CREATE INDEX idx_health_project ON project_health_snapshots(project_id);
CREATE INDEX idx_health_date ON project_health_snapshots(snapshot_date);

-- ============================================
-- 9. 预警规则模板表
-- ============================================

CREATE TABLE IF NOT EXISTS alert_rule_templates (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code       VARCHAR(50) NOT NULL UNIQUE,          -- 模板编码
    template_name       VARCHAR(200) NOT NULL,                -- 模板名称
    template_category   VARCHAR(30) NOT NULL,                 -- 模板分类

    -- 规则配置
    rule_config         TEXT NOT NULL,                        -- 规则配置JSON

    -- 说明
    description         TEXT,                                 -- 模板说明
    usage_guide         TEXT,                                 -- 使用指南

    is_active           BOOLEAN DEFAULT 1,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 10. 视图定义
-- ============================================

-- 待处理预警视图
CREATE VIEW IF NOT EXISTS v_pending_alerts AS
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
    JULIANDAY('now') - JULIANDAY(ar.triggered_at) as pending_days
FROM alert_records ar
LEFT JOIN projects p ON ar.project_id = p.id
LEFT JOIN users u ON ar.handler_id = u.id
LEFT JOIN alert_rules r ON ar.rule_id = r.id
WHERE ar.status IN ('PENDING', 'ACKNOWLEDGED', 'PROCESSING');

-- 未关闭异常视图
CREATE VIEW IF NOT EXISTS v_open_exceptions AS
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
    JULIANDAY('now') - JULIANDAY(ee.discovered_at) as open_days
FROM exception_events ee
LEFT JOIN projects p ON ee.project_id = p.id
LEFT JOIN machines m ON ee.machine_id = m.id
LEFT JOIN users u ON ee.responsible_user_id = u.id
WHERE ee.status NOT IN ('CLOSED', 'DEFERRED');

-- ============================================
-- 完成
-- ============================================
