-- ============================================
-- 项目管理模块 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2025-07-12
-- 说明: 项目、设备、阶段、状态、成员等核心表
-- ============================================

-- ============================================
-- 1. 项目主表
-- ============================================

CREATE TABLE IF NOT EXISTS projects (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_code        VARCHAR(50) NOT NULL UNIQUE,          -- 项目编码
    project_name        VARCHAR(200) NOT NULL,                -- 项目名称
    short_name          VARCHAR(50),                          -- 项目简称

    -- 客户信息
    customer_id         INTEGER,                              -- 客户ID
    customer_name       VARCHAR(200),                         -- 客户名称（冗余）
    customer_contact    VARCHAR(100),                         -- 客户联系人
    customer_phone      VARCHAR(50),                          -- 联系电话

    -- 合同信息
    contract_no         VARCHAR(100),                         -- 合同编号
    contract_amount     DECIMAL(14,2),                        -- 合同金额
    contract_date       DATE,                                 -- 合同签订日期

    -- 项目类型与分类
    project_type        VARCHAR(50) DEFAULT 'STANDARD',       -- 项目类型：STANDARD/UPGRADE/MAINTENANCE
    product_category    VARCHAR(50),                          -- 产品类别：ASSEMBLY_LINE/INSPECTION/PACKAGING等
    industry            VARCHAR(50),                          -- 行业：3C/AUTO/MEDICAL/FOOD等

    -- 三维状态
    stage               VARCHAR(20) DEFAULT 'S1',             -- 阶段：S1-S9
    status              VARCHAR(20) DEFAULT 'ST01',           -- 状态：每阶段细分状态
    health              VARCHAR(10) DEFAULT 'H1',             -- 健康度：H1-H4

    -- 时间计划
    planned_start_date  DATE,                                 -- 计划开始日期
    planned_end_date    DATE,                                 -- 计划结束日期
    actual_start_date   DATE,                                 -- 实际开始日期
    actual_end_date     DATE,                                 -- 实际结束日期

    -- 进度信息
    progress_pct        DECIMAL(5,2) DEFAULT 0,               -- 整体进度百分比

    -- 预算与成本
    budget_amount       DECIMAL(14,2),                        -- 预算金额
    actual_cost         DECIMAL(14,2) DEFAULT 0,              -- 实际成本

    -- 项目团队
    pm_id               INTEGER,                              -- 项目经理ID
    pm_name             VARCHAR(50),                          -- 项目经理姓名（冗余）
    dept_id             INTEGER,                              -- 所属部门

    -- 优先级与标签
    priority            VARCHAR(20) DEFAULT 'NORMAL',         -- 优先级：LOW/NORMAL/HIGH/URGENT
    tags                TEXT,                                 -- 标签JSON数组

    -- 描述
    description         TEXT,                                 -- 项目描述
    requirements        TEXT,                                 -- 项目需求摘要

    -- 附件
    attachments         TEXT,                                 -- 附件列表JSON

    -- 状态
    is_active           BOOLEAN DEFAULT 1,                    -- 是否激活
    is_archived         BOOLEAN DEFAULT 0,                    -- 是否归档

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (pm_id) REFERENCES users(id),
    FOREIGN KEY (dept_id) REFERENCES departments(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_projects_code ON projects(project_code);
CREATE INDEX idx_projects_customer ON projects(customer_id);
CREATE INDEX idx_projects_pm ON projects(pm_id);
CREATE INDEX idx_projects_stage ON projects(stage);
CREATE INDEX idx_projects_health ON projects(health);
CREATE INDEX idx_projects_active ON projects(is_active);

-- ============================================
-- 2. 设备/机台表
-- ============================================

CREATE TABLE IF NOT EXISTS machines (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 所属项目
    machine_code        VARCHAR(50) NOT NULL,                 -- 设备编码
    machine_name        VARCHAR(200) NOT NULL,                -- 设备名称
    machine_no          INTEGER DEFAULT 1,                    -- 设备序号（项目内）

    -- 设备类型
    machine_type        VARCHAR(50),                          -- 设备类型
    specification       TEXT,                                 -- 规格描述

    -- 状态
    stage               VARCHAR(20) DEFAULT 'S1',             -- 设备阶段
    status              VARCHAR(20) DEFAULT 'ST01',           -- 设备状态
    health              VARCHAR(10) DEFAULT 'H1',             -- 健康度

    -- 进度
    progress_pct        DECIMAL(5,2) DEFAULT 0,               -- 设备进度

    -- 时间
    planned_start_date  DATE,                                 -- 计划开始
    planned_end_date    DATE,                                 -- 计划结束
    actual_start_date   DATE,                                 -- 实际开始
    actual_end_date     DATE,                                 -- 实际结束

    -- FAT/SAT信息
    fat_date            DATE,                                 -- FAT日期
    fat_result          VARCHAR(20),                          -- FAT结果
    sat_date            DATE,                                 -- SAT日期
    sat_result          VARCHAR(20),                          -- SAT结果

    -- 发货信息
    ship_date           DATE,                                 -- 发货日期
    ship_address        VARCHAR(500),                         -- 发货地址
    tracking_no         VARCHAR(100),                         -- 物流单号

    -- 备注
    remark              TEXT,

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    UNIQUE(project_id, machine_code)
);

CREATE INDEX idx_machines_project ON machines(project_id);
CREATE INDEX idx_machines_stage ON machines(stage);

-- ============================================
-- 3. 项目阶段定义表（系统配置）
-- ============================================

CREATE TABLE IF NOT EXISTS project_stages (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_code          VARCHAR(20) NOT NULL UNIQUE,          -- 阶段编码：S1-S9
    stage_name          VARCHAR(50) NOT NULL,                 -- 阶段名称
    stage_order         INTEGER NOT NULL,                     -- 阶段顺序
    description         TEXT,                                 -- 阶段描述

    -- 门控条件
    gate_conditions     TEXT,                                 -- 进入条件JSON
    required_deliverables TEXT,                               -- 必需交付物JSON

    -- 默认时长
    default_duration_days INTEGER,                            -- 默认工期（天）

    -- 颜色配置
    color               VARCHAR(20),                          -- 显示颜色
    icon                VARCHAR(50),                          -- 图标

    is_active           BOOLEAN DEFAULT 1,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 4. 项目状态定义表（系统配置）
-- ============================================

CREATE TABLE IF NOT EXISTS project_statuses (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_code          VARCHAR(20) NOT NULL,                 -- 所属阶段
    status_code         VARCHAR(20) NOT NULL UNIQUE,          -- 状态编码
    status_name         VARCHAR(50) NOT NULL,                 -- 状态名称
    status_order        INTEGER NOT NULL,                     -- 状态顺序
    description         TEXT,                                 -- 状态描述

    -- 状态类型
    status_type         VARCHAR(20) DEFAULT 'NORMAL',         -- NORMAL/MILESTONE/GATE

    -- 自动流转
    auto_next_status    VARCHAR(20),                          -- 自动下一状态

    is_active           BOOLEAN DEFAULT 1,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (stage_code) REFERENCES project_stages(stage_code)
);

CREATE INDEX idx_project_statuses_stage ON project_statuses(stage_code);

-- ============================================
-- 5. 项目状态变更日志
-- ============================================

CREATE TABLE IF NOT EXISTS project_status_logs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID
    machine_id          INTEGER,                              -- 设备ID（可选）

    -- 变更前状态
    old_stage           VARCHAR(20),
    old_status          VARCHAR(20),
    old_health          VARCHAR(10),

    -- 变更后状态
    new_stage           VARCHAR(20),
    new_status          VARCHAR(20),
    new_health          VARCHAR(10),

    -- 变更信息
    change_type         VARCHAR(20) NOT NULL,                 -- STAGE_CHANGE/STATUS_CHANGE/HEALTH_CHANGE
    change_reason       TEXT,                                 -- 变更原因
    change_note         TEXT,                                 -- 变更备注

    -- 操作信息
    changed_by          INTEGER,
    changed_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (changed_by) REFERENCES users(id)
);

CREATE INDEX idx_project_status_logs_project ON project_status_logs(project_id);
CREATE INDEX idx_project_status_logs_machine ON project_status_logs(machine_id);
CREATE INDEX idx_project_status_logs_time ON project_status_logs(changed_at);

-- ============================================
-- 6. 项目成员表
-- ============================================

CREATE TABLE IF NOT EXISTS project_members (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID
    user_id             INTEGER NOT NULL,                     -- 用户ID
    role_code           VARCHAR(50) NOT NULL,                 -- 角色编码

    -- 分配信息
    allocation_pct      DECIMAL(5,2) DEFAULT 100,             -- 分配比例
    start_date          DATE,                                 -- 开始日期
    end_date            DATE,                                 -- 结束日期

    -- 状态
    is_active           BOOLEAN DEFAULT 1,

    -- 备注
    remark              TEXT,

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (role_code) REFERENCES roles(role_code),
    FOREIGN KEY (created_by) REFERENCES users(id),
    UNIQUE(project_id, user_id, role_code)
);

CREATE INDEX idx_project_members_project ON project_members(project_id);
CREATE INDEX idx_project_members_user ON project_members(user_id);

-- ============================================
-- 7. 项目里程碑表
-- ============================================

CREATE TABLE IF NOT EXISTS project_milestones (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID
    machine_id          INTEGER,                              -- 设备ID（可选）

    milestone_code      VARCHAR(50) NOT NULL,                 -- 里程碑编码
    milestone_name      VARCHAR(200) NOT NULL,                -- 里程碑名称
    milestone_type      VARCHAR(20) DEFAULT 'CUSTOM',         -- GATE/DELIVERY/PAYMENT/CUSTOM

    -- 时间
    planned_date        DATE NOT NULL,                        -- 计划日期
    actual_date         DATE,                                 -- 实际完成日期

    -- 状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/IN_PROGRESS/COMPLETED/DELAYED

    -- 关联阶段
    stage_code          VARCHAR(20),                          -- 关联阶段

    -- 交付物
    deliverables        TEXT,                                 -- 交付物JSON

    -- 责任人
    owner_id            INTEGER,

    -- 备注
    description         TEXT,
    completion_note     TEXT,

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

CREATE INDEX idx_project_milestones_project ON project_milestones(project_id);
CREATE INDEX idx_project_milestones_status ON project_milestones(status);
CREATE INDEX idx_project_milestones_date ON project_milestones(planned_date);

-- ============================================
-- 8. 项目回款计划表
-- ============================================

CREATE TABLE IF NOT EXISTS project_payment_plans (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID

    payment_no          INTEGER NOT NULL,                     -- 期次
    payment_name        VARCHAR(100) NOT NULL,                -- 款项名称（如：预付款、发货款）
    payment_type        VARCHAR(20) NOT NULL,                 -- ADVANCE/DELIVERY/ACCEPTANCE/WARRANTY

    -- 金额
    payment_ratio       DECIMAL(5,2),                         -- 比例(%)
    planned_amount      DECIMAL(14,2) NOT NULL,               -- 计划金额
    actual_amount       DECIMAL(14,2) DEFAULT 0,              -- 实际收款

    -- 时间
    planned_date        DATE,                                 -- 计划收款日期
    actual_date         DATE,                                 -- 实际收款日期

    -- 触发条件
    trigger_milestone   VARCHAR(50),                          -- 触发里程碑
    trigger_condition   TEXT,                                 -- 触发条件描述

    -- 状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/INVOICED/PARTIAL/COMPLETED

    -- 发票信息
    invoice_no          VARCHAR(100),                         -- 发票号
    invoice_date        DATE,                                 -- 开票日期
    invoice_amount      DECIMAL(14,2),                        -- 开票金额

    remark              TEXT,

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX idx_project_payment_plans_project ON project_payment_plans(project_id);
CREATE INDEX idx_project_payment_plans_status ON project_payment_plans(status);

-- ============================================
-- 9. 项目成本记录表
-- ============================================

CREATE TABLE IF NOT EXISTS project_costs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID
    machine_id          INTEGER,                              -- 设备ID（可选）

    cost_type           VARCHAR(50) NOT NULL,                 -- 成本类型
    cost_category       VARCHAR(50) NOT NULL,                 -- 成本分类

    -- 来源
    source_module       VARCHAR(50),                          -- 来源模块
    source_type         VARCHAR(50),                          -- 来源类型
    source_id           INTEGER,                              -- 来源ID
    source_no           VARCHAR(100),                         -- 来源单号

    -- 金额
    amount              DECIMAL(14,2) NOT NULL,               -- 金额
    tax_amount          DECIMAL(12,2) DEFAULT 0,              -- 税额

    -- 描述
    description         TEXT,                                 -- 描述

    -- 时间
    cost_date           DATE NOT NULL,                        -- 成本日期

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_project_costs_project ON project_costs(project_id);
CREATE INDEX idx_project_costs_type ON project_costs(cost_type);
CREATE INDEX idx_project_costs_date ON project_costs(cost_date);

-- ============================================
-- 10. 项目文档表
-- ============================================

CREATE TABLE IF NOT EXISTS project_documents (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID
    machine_id          INTEGER,                              -- 设备ID（可选）

    doc_type            VARCHAR(50) NOT NULL,                 -- 文档类型
    doc_category        VARCHAR(50),                          -- 文档分类
    doc_name            VARCHAR(200) NOT NULL,                -- 文档名称
    doc_no              VARCHAR(100),                         -- 文档编号
    version             VARCHAR(20) DEFAULT '1.0',            -- 版本号

    -- 文件信息
    file_path           VARCHAR(500) NOT NULL,                -- 文件路径
    file_name           VARCHAR(200) NOT NULL,                -- 原始文件名
    file_size           INTEGER,                              -- 文件大小
    file_type           VARCHAR(50),                          -- 文件类型

    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT',          -- DRAFT/REVIEW/APPROVED/RELEASED

    -- 审批
    approved_by         INTEGER,
    approved_at         DATETIME,

    -- 描述
    description         TEXT,

    uploaded_by         INTEGER,
    uploaded_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

CREATE INDEX idx_project_documents_project ON project_documents(project_id);
CREATE INDEX idx_project_documents_type ON project_documents(doc_type);

-- ============================================
-- 11. 客户表（基础数据）
-- ============================================

CREATE TABLE IF NOT EXISTS customers (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_code       VARCHAR(50) NOT NULL UNIQUE,          -- 客户编码
    customer_name       VARCHAR(200) NOT NULL,                -- 客户名称
    short_name          VARCHAR(50),                          -- 简称

    -- 基本信息
    customer_type       VARCHAR(20) DEFAULT 'ENTERPRISE',     -- ENTERPRISE/INDIVIDUAL
    industry            VARCHAR(50),                          -- 行业
    scale               VARCHAR(20),                          -- 规模

    -- 联系信息
    contact_person      VARCHAR(50),                          -- 联系人
    contact_phone       VARCHAR(50),                          -- 联系电话
    contact_email       VARCHAR(100),                         -- 邮箱
    address             VARCHAR(500),                         -- 地址

    -- 公司信息
    legal_person        VARCHAR(50),                          -- 法人
    tax_no              VARCHAR(50),                          -- 税号
    bank_name           VARCHAR(100),                         -- 开户银行
    bank_account        VARCHAR(50),                          -- 银行账号

    -- 信用信息
    credit_level        VARCHAR(20),                          -- 信用等级
    credit_limit        DECIMAL(14,2),                        -- 信用额度
    payment_terms       VARCHAR(50),                          -- 付款条款

    -- 客户门户
    portal_enabled      BOOLEAN DEFAULT 0,                    -- 是否启用门户
    portal_username     VARCHAR(100),                         -- 门户账号

    -- 状态
    status              VARCHAR(20) DEFAULT 'ACTIVE',         -- ACTIVE/INACTIVE

    -- 备注
    remark              TEXT,

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_customers_code ON customers(customer_code);
CREATE INDEX idx_customers_name ON customers(customer_name);
CREATE INDEX idx_customers_industry ON customers(industry);

-- ============================================
-- 12. 视图定义
-- ============================================

-- 项目概览视图
CREATE VIEW IF NOT EXISTS v_project_overview AS
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
CREATE VIEW IF NOT EXISTS v_project_progress AS
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
    CASE
        WHEN p.actual_end_date IS NOT NULL THEN julianday(p.actual_end_date) - julianday(p.planned_end_date)
        ELSE julianday('now') - julianday(p.planned_end_date)
    END as delay_days
FROM projects p
WHERE p.is_active = 1;

-- ============================================
-- 完成
-- ============================================
