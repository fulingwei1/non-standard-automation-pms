-- ============================================
-- 变更管理模块(ECN) - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-02
-- 说明: ECN主表、评估、审批、任务、影响追溯等
-- ============================================

-- ============================================
-- 1. ECN主表
-- ============================================

CREATE TABLE IF NOT EXISTS ecn (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_no              VARCHAR(50) NOT NULL UNIQUE,          -- ECN编号
    ecn_title           VARCHAR(200) NOT NULL,                -- ECN标题
    ecn_type            VARCHAR(20) NOT NULL,                 -- 变更类型

    -- 来源
    source_type         VARCHAR(20) NOT NULL,                 -- 来源类型
    source_no           VARCHAR(100),                         -- 来源单号
    source_id           INTEGER,                              -- 来源ID

    -- 关联
    project_id          INTEGER NOT NULL,                     -- 项目ID
    machine_id          INTEGER,                              -- 设备ID

    -- 变更内容
    change_reason       TEXT NOT NULL,                        -- 变更原因
    change_description  TEXT NOT NULL,                        -- 变更内容描述
    change_scope        VARCHAR(20) DEFAULT 'PARTIAL',        -- 变更范围

    -- 优先级
    priority            VARCHAR(20) DEFAULT 'NORMAL',         -- 优先级
    urgency             VARCHAR(20) DEFAULT 'NORMAL',         -- 紧急程度

    -- 影响评估
    cost_impact         DECIMAL(14,2) DEFAULT 0,              -- 成本影响
    schedule_impact_days INTEGER DEFAULT 0,                   -- 工期影响(天)
    quality_impact      VARCHAR(20),                          -- 质量影响

    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT',          -- 状态
    current_step        VARCHAR(50),                          -- 当前步骤

    -- 申请人
    applicant_id        INTEGER,                              -- 申请人
    applicant_dept      VARCHAR(100),                         -- 申请部门
    applied_at          DATETIME,                             -- 申请时间

    -- 审批结果
    approval_result     VARCHAR(20),                          -- 审批结果
    approval_note       TEXT,                                 -- 审批意见
    approved_at         DATETIME,                             -- 审批时间

    -- 执行
    execution_start     DATETIME,                             -- 执行开始
    execution_end       DATETIME,                             -- 执行结束
    execution_note      TEXT,                                 -- 执行说明

    -- 关闭
    closed_at           DATETIME,                             -- 关闭时间
    closed_by           INTEGER,                              -- 关闭人

    -- 附件
    attachments         TEXT,                                 -- 附件JSON

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (applicant_id) REFERENCES users(id),
    FOREIGN KEY (closed_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_ecn_no ON ecn(ecn_no);
CREATE INDEX idx_ecn_project ON ecn(project_id);
CREATE INDEX idx_ecn_status ON ecn(status);
CREATE INDEX idx_ecn_type ON ecn(ecn_type);
CREATE INDEX idx_ecn_applicant ON ecn(applicant_id);

-- ============================================
-- 2. ECN评估表
-- ============================================

CREATE TABLE IF NOT EXISTS ecn_evaluations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_id              INTEGER NOT NULL,                     -- ECN ID
    eval_dept           VARCHAR(50) NOT NULL,                 -- 评估部门

    -- 评估人
    evaluator_id        INTEGER,                              -- 评估人
    evaluator_name      VARCHAR(50),                          -- 评估人姓名

    -- 评估内容
    impact_analysis     TEXT,                                 -- 影响分析
    cost_estimate       DECIMAL(14,2) DEFAULT 0,              -- 成本估算
    schedule_estimate   INTEGER DEFAULT 0,                    -- 工期估算(天)
    resource_requirement TEXT,                                -- 资源需求
    risk_assessment     TEXT,                                 -- 风险评估

    -- 评估结论
    eval_result         VARCHAR(20),                          -- APPROVE/REJECT/CONDITIONAL
    eval_opinion        TEXT,                                 -- 评估意见
    conditions          TEXT,                                 -- 附加条件

    -- 状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/COMPLETED/SKIPPED
    evaluated_at        DATETIME,                             -- 评估时间

    -- 附件
    attachments         TEXT,

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ecn_id) REFERENCES ecn(id),
    FOREIGN KEY (evaluator_id) REFERENCES users(id)
);

CREATE INDEX idx_ecn_evaluations_ecn ON ecn_evaluations(ecn_id);
CREATE INDEX idx_ecn_evaluations_dept ON ecn_evaluations(eval_dept);
CREATE INDEX idx_ecn_evaluations_status ON ecn_evaluations(status);

-- ============================================
-- 3. ECN审批表
-- ============================================

CREATE TABLE IF NOT EXISTS ecn_approvals (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_id              INTEGER NOT NULL,                     -- ECN ID
    approval_level      INTEGER NOT NULL,                     -- 审批层级
    approval_role       VARCHAR(50) NOT NULL,                 -- 审批角色

    -- 审批人
    approver_id         INTEGER,                              -- 审批人ID
    approver_name       VARCHAR(50),                          -- 审批人姓名

    -- 审批结果
    approval_result     VARCHAR(20),                          -- APPROVED/REJECTED/RETURNED
    approval_opinion    TEXT,                                 -- 审批意见

    -- 状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/COMPLETED
    approved_at         DATETIME,                             -- 审批时间

    -- 超时
    due_date            DATETIME,                             -- 审批期限
    is_overdue          BOOLEAN DEFAULT 0,                    -- 是否超期

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ecn_id) REFERENCES ecn(id),
    FOREIGN KEY (approver_id) REFERENCES users(id)
);

CREATE INDEX idx_ecn_approvals_ecn ON ecn_approvals(ecn_id);
CREATE INDEX idx_ecn_approvals_approver ON ecn_approvals(approver_id);
CREATE INDEX idx_ecn_approvals_status ON ecn_approvals(status);

-- ============================================
-- 4. ECN执行任务表
-- ============================================

CREATE TABLE IF NOT EXISTS ecn_tasks (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_id              INTEGER NOT NULL,                     -- ECN ID
    task_no             INTEGER NOT NULL,                     -- 任务序号
    task_name           VARCHAR(200) NOT NULL,                -- 任务名称
    task_type           VARCHAR(50),                          -- 任务类型
    task_dept           VARCHAR(50),                          -- 责任部门

    -- 任务内容
    task_description    TEXT,                                 -- 任务描述
    deliverables        TEXT,                                 -- 交付物要求

    -- 负责人
    assignee_id         INTEGER,                              -- 负责人
    assignee_name       VARCHAR(50),                          -- 负责人姓名

    -- 时间
    planned_start       DATE,                                 -- 计划开始
    planned_end         DATE,                                 -- 计划结束
    actual_start        DATE,                                 -- 实际开始
    actual_end          DATE,                                 -- 实际结束

    -- 进度
    progress_pct        INTEGER DEFAULT 0,                    -- 进度百分比

    -- 状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/IN_PROGRESS/COMPLETED/CANCELLED

    -- 完成信息
    completion_note     TEXT,                                 -- 完成说明
    attachments         TEXT,                                 -- 附件

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ecn_id) REFERENCES ecn(id),
    FOREIGN KEY (assignee_id) REFERENCES users(id)
);

CREATE INDEX idx_ecn_tasks_ecn ON ecn_tasks(ecn_id);
CREATE INDEX idx_ecn_tasks_assignee ON ecn_tasks(assignee_id);
CREATE INDEX idx_ecn_tasks_status ON ecn_tasks(status);

-- ============================================
-- 5. ECN受影响物料表
-- ============================================

CREATE TABLE IF NOT EXISTS ecn_affected_materials (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_id              INTEGER NOT NULL,                     -- ECN ID
    material_id         INTEGER,                              -- 物料ID
    bom_item_id         INTEGER,                              -- BOM行ID

    -- 物料信息
    material_code       VARCHAR(50) NOT NULL,
    material_name       VARCHAR(200) NOT NULL,
    specification       VARCHAR(500),

    -- 变更类型
    change_type         VARCHAR(20) NOT NULL,                 -- ADD/DELETE/MODIFY/REPLACE

    -- 变更前
    old_quantity        DECIMAL(10,4),
    old_specification   VARCHAR(500),
    old_supplier_id     INTEGER,

    -- 变更后
    new_quantity        DECIMAL(10,4),
    new_specification   VARCHAR(500),
    new_supplier_id     INTEGER,

    -- 影响
    cost_impact         DECIMAL(12,2) DEFAULT 0,              -- 成本影响

    -- 处理状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/PROCESSED
    processed_at        DATETIME,

    remark              TEXT,

    FOREIGN KEY (ecn_id) REFERENCES ecn(id),
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (bom_item_id) REFERENCES bom_items(id)
);

CREATE INDEX idx_ecn_materials_ecn ON ecn_affected_materials(ecn_id);
CREATE INDEX idx_ecn_materials_material ON ecn_affected_materials(material_id);

-- ============================================
-- 6. ECN受影响采购订单表
-- ============================================

CREATE TABLE IF NOT EXISTS ecn_affected_orders (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_id              INTEGER NOT NULL,                     -- ECN ID
    order_type          VARCHAR(20) NOT NULL,                 -- PURCHASE/OUTSOURCE
    order_id            INTEGER NOT NULL,                     -- 订单ID
    order_no            VARCHAR(50) NOT NULL,                 -- 订单号

    -- 影响描述
    impact_description  TEXT,                                 -- 影响描述

    -- 处理方式
    action_type         VARCHAR(20),                          -- CANCEL/MODIFY/KEEP
    action_description  TEXT,                                 -- 处理说明

    -- 处理状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/PROCESSED
    processed_by        INTEGER,
    processed_at        DATETIME,

    FOREIGN KEY (ecn_id) REFERENCES ecn(id),
    FOREIGN KEY (processed_by) REFERENCES users(id)
);

CREATE INDEX idx_ecn_orders_ecn ON ecn_affected_orders(ecn_id);

-- ============================================
-- 7. ECN流转日志表
-- ============================================

CREATE TABLE IF NOT EXISTS ecn_logs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_id              INTEGER NOT NULL,                     -- ECN ID
    log_type            VARCHAR(20) NOT NULL,                 -- 日志类型
    log_action          VARCHAR(50) NOT NULL,                 -- 操作动作

    -- 状态变更
    old_status          VARCHAR(20),
    new_status          VARCHAR(20),

    -- 内容
    log_content         TEXT,                                 -- 日志内容
    attachments         TEXT,                                 -- 附件

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ecn_id) REFERENCES ecn(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_ecn_logs_ecn ON ecn_logs(ecn_id);
CREATE INDEX idx_ecn_logs_time ON ecn_logs(created_at);

-- ============================================
-- 8. ECN类型配置表
-- ============================================

CREATE TABLE IF NOT EXISTS ecn_types (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    type_code           VARCHAR(20) NOT NULL UNIQUE,          -- 类型编码
    type_name           VARCHAR(50) NOT NULL,                 -- 类型名称
    description         TEXT,                                 -- 描述

    -- 评估配置
    required_depts      TEXT,                                 -- 必需评估部门JSON
    optional_depts      TEXT,                                 -- 可选评估部门JSON

    -- 审批配置
    approval_matrix     TEXT,                                 -- 审批矩阵JSON

    is_active           BOOLEAN DEFAULT 1,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 9. ECN审批矩阵配置表
-- ============================================

CREATE TABLE IF NOT EXISTS ecn_approval_matrix (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_type            VARCHAR(20),                          -- ECN类型
    condition_type      VARCHAR(20) NOT NULL,                 -- 条件类型：COST/SCHEDULE
    condition_min       DECIMAL(14,2),                        -- 条件下限
    condition_max       DECIMAL(14,2),                        -- 条件上限

    approval_level      INTEGER NOT NULL,                     -- 审批层级
    approval_role       VARCHAR(50) NOT NULL,                 -- 审批角色

    is_active           BOOLEAN DEFAULT 1,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ecn_matrix_type ON ecn_approval_matrix(ecn_type);

-- ============================================
-- 10. 视图定义
-- ============================================

-- ECN概览视图
CREATE VIEW IF NOT EXISTS v_ecn_overview AS
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

-- ============================================
-- 完成
-- ============================================
