-- ============================================
-- 验收管理模块 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-02
-- 说明: 验收模板、验收单、检查项、问题、签字等
-- ============================================

-- ============================================
-- 1. 验收模板表
-- ============================================

CREATE TABLE IF NOT EXISTS acceptance_templates (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code       VARCHAR(50) NOT NULL UNIQUE,          -- 模板编码
    template_name       VARCHAR(200) NOT NULL,                -- 模板名称
    acceptance_type     VARCHAR(20) NOT NULL,                 -- FAT/SAT/FINAL
    equipment_type      VARCHAR(50),                          -- 设备类型
    version             VARCHAR(20) DEFAULT '1.0',            -- 版本号
    description         TEXT,                                 -- 模板说明
    is_system           BOOLEAN DEFAULT 0,                    -- 是否系统预置
    is_active           BOOLEAN DEFAULT 1,                    -- 是否启用
    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_templates_type ON acceptance_templates(acceptance_type);
CREATE INDEX idx_templates_equip ON acceptance_templates(equipment_type);

-- ============================================
-- 2. 模板检查分类表
-- ============================================

CREATE TABLE IF NOT EXISTS template_categories (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id         INTEGER NOT NULL,                     -- 所属模板
    category_code       VARCHAR(20) NOT NULL,                 -- 分类编码
    category_name       VARCHAR(100) NOT NULL,                -- 分类名称
    weight              DECIMAL(5,2) DEFAULT 0,               -- 权重百分比
    sort_order          INTEGER DEFAULT 0,                    -- 排序
    is_required         BOOLEAN DEFAULT 1,                    -- 是否必检分类
    description         TEXT,                                 -- 分类说明

    FOREIGN KEY (template_id) REFERENCES acceptance_templates(id),
    UNIQUE(template_id, category_code)
);

-- ============================================
-- 3. 模板检查项表
-- ============================================

CREATE TABLE IF NOT EXISTS template_check_items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id         INTEGER NOT NULL,                     -- 所属分类
    item_code           VARCHAR(50) NOT NULL,                 -- 检查项编码
    item_name           VARCHAR(200) NOT NULL,                -- 检查项名称
    check_method        TEXT,                                 -- 检查方法
    acceptance_criteria TEXT,                                 -- 验收标准
    standard_value      VARCHAR(100),                         -- 标准值
    tolerance_min       VARCHAR(50),                          -- 下限
    tolerance_max       VARCHAR(50),                          -- 上限
    unit                VARCHAR(20),                          -- 单位
    is_required         BOOLEAN DEFAULT 1,                    -- 是否必检项
    is_key_item         BOOLEAN DEFAULT 0,                    -- 是否关键项
    sort_order          INTEGER DEFAULT 0,                    -- 排序

    FOREIGN KEY (category_id) REFERENCES template_categories(id)
);

CREATE INDEX idx_check_items_category ON template_check_items(category_id);

-- ============================================
-- 4. 验收单表
-- ============================================

CREATE TABLE IF NOT EXISTS acceptance_orders (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no            VARCHAR(50) NOT NULL UNIQUE,          -- 验收单号
    project_id          INTEGER NOT NULL,                     -- 项目ID
    machine_id          INTEGER,                              -- 设备ID
    acceptance_type     VARCHAR(20) NOT NULL,                 -- FAT/SAT/FINAL
    template_id         INTEGER,                              -- 使用的模板

    -- 验收信息
    planned_date        DATE,                                 -- 计划验收日期
    actual_start_date   DATETIME,                             -- 实际开始时间
    actual_end_date     DATETIME,                             -- 实际结束时间
    location            VARCHAR(200),                         -- 验收地点

    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT',          -- 验收状态

    -- 统计
    total_items         INTEGER DEFAULT 0,                    -- 检查项总数
    passed_items        INTEGER DEFAULT 0,                    -- 通过项数
    failed_items        INTEGER DEFAULT 0,                    -- 不通过项数
    na_items            INTEGER DEFAULT 0,                    -- 不适用项数
    pass_rate           DECIMAL(5,2) DEFAULT 0,               -- 通过率

    -- 结论
    overall_result      VARCHAR(20),                          -- PASSED/FAILED/CONDITIONAL
    conclusion          TEXT,                                 -- 验收结论
    conditions          TEXT,                                 -- 有条件通过的条件说明

    -- 签字确认
    qa_signer_id        INTEGER,                              -- QA签字人
    qa_signed_at        DATETIME,                             -- QA签字时间
    customer_signer     VARCHAR(100),                         -- 客户签字人
    customer_signed_at  DATETIME,                             -- 客户签字时间
    customer_signature  TEXT,                                 -- 客户电子签名

    -- 附件
    report_file_path    VARCHAR(500),                         -- 验收报告文件路径

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (template_id) REFERENCES acceptance_templates(id),
    FOREIGN KEY (qa_signer_id) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_orders_project ON acceptance_orders(project_id);
CREATE INDEX idx_orders_machine ON acceptance_orders(machine_id);
CREATE INDEX idx_orders_status ON acceptance_orders(status);
CREATE INDEX idx_orders_type ON acceptance_orders(acceptance_type);

-- ============================================
-- 5. 验收单检查项表
-- ============================================

CREATE TABLE IF NOT EXISTS acceptance_order_items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id            INTEGER NOT NULL,                     -- 验收单ID
    template_item_id    INTEGER,                              -- 模板检查项ID

    -- 检查项信息
    category_code       VARCHAR(20) NOT NULL,
    category_name       VARCHAR(100) NOT NULL,
    item_code           VARCHAR(50) NOT NULL,
    item_name           VARCHAR(200) NOT NULL,
    check_method        TEXT,
    acceptance_criteria TEXT,
    standard_value      VARCHAR(100),
    tolerance_min       VARCHAR(50),
    tolerance_max       VARCHAR(50),
    unit                VARCHAR(20),
    is_required         BOOLEAN DEFAULT 1,
    is_key_item         BOOLEAN DEFAULT 0,
    sort_order          INTEGER DEFAULT 0,

    -- 检查结果
    result_status       VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/PASSED/FAILED/NA/CONDITIONAL
    actual_value        VARCHAR(100),                         -- 实际值
    deviation           VARCHAR(100),                         -- 偏差
    remark              TEXT,                                 -- 备注

    -- 检查记录
    checked_by          INTEGER,                              -- 检查人
    checked_at          DATETIME,                             -- 检查时间

    -- 复验信息
    retry_count         INTEGER DEFAULT 0,                    -- 复验次数
    last_retry_at       DATETIME,                             -- 最后复验时间

    FOREIGN KEY (order_id) REFERENCES acceptance_orders(id),
    FOREIGN KEY (template_item_id) REFERENCES template_check_items(id),
    FOREIGN KEY (checked_by) REFERENCES users(id)
);

CREATE INDEX idx_order_items_order ON acceptance_order_items(order_id);
CREATE INDEX idx_order_items_status ON acceptance_order_items(result_status);

-- ============================================
-- 6. 验收问题表
-- ============================================

CREATE TABLE IF NOT EXISTS acceptance_issues (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_no            VARCHAR(50) NOT NULL UNIQUE,          -- 问题编号
    order_id            INTEGER NOT NULL,                     -- 验收单ID
    order_item_id       INTEGER,                              -- 关联检查项

    -- 问题信息
    issue_type          VARCHAR(20) NOT NULL,                 -- DEFECT/DEVIATION/SUGGESTION
    severity            VARCHAR(20) NOT NULL,                 -- CRITICAL/MAJOR/MINOR
    title               VARCHAR(200) NOT NULL,                -- 问题标题
    description         TEXT NOT NULL,                        -- 问题描述
    found_at            DATETIME DEFAULT CURRENT_TIMESTAMP,   -- 发现时间
    found_by            INTEGER,                              -- 发现人

    -- 处理信息
    status              VARCHAR(20) DEFAULT 'OPEN',           -- OPEN/PROCESSING/RESOLVED/CLOSED/DEFERRED
    assigned_to         INTEGER,                              -- 处理负责人
    due_date            DATE,                                 -- 要求完成日期

    -- 解决信息
    solution            TEXT,                                 -- 解决方案
    resolved_at         DATETIME,                             -- 解决时间
    resolved_by         INTEGER,                              -- 解决人

    -- 验证信息
    verified_at         DATETIME,                             -- 验证时间
    verified_by         INTEGER,                              -- 验证人
    verified_result     VARCHAR(20),                          -- VERIFIED/REJECTED

    -- 是否阻塞验收
    is_blocking         BOOLEAN DEFAULT 0,                    -- 是否阻塞验收通过

    -- 附件
    attachments         TEXT,                                 -- 附件列表JSON

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (order_id) REFERENCES acceptance_orders(id),
    FOREIGN KEY (order_item_id) REFERENCES acceptance_order_items(id),
    FOREIGN KEY (found_by) REFERENCES users(id),
    FOREIGN KEY (assigned_to) REFERENCES users(id),
    FOREIGN KEY (resolved_by) REFERENCES users(id),
    FOREIGN KEY (verified_by) REFERENCES users(id)
);

CREATE INDEX idx_issues_order ON acceptance_issues(order_id);
CREATE INDEX idx_issues_status ON acceptance_issues(status);
CREATE INDEX idx_issues_severity ON acceptance_issues(severity);
CREATE INDEX idx_issues_assigned ON acceptance_issues(assigned_to);

-- ============================================
-- 7. 问题跟进记录表
-- ============================================

CREATE TABLE IF NOT EXISTS issue_follow_ups (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id            INTEGER NOT NULL,                     -- 问题ID
    action_type         VARCHAR(20) NOT NULL,                 -- COMMENT/STATUS_CHANGE/ASSIGN/RESOLVE/VERIFY
    action_content      TEXT NOT NULL,                        -- 操作内容
    old_value           VARCHAR(100),                         -- 原值
    new_value           VARCHAR(100),                         -- 新值
    attachments         TEXT,                                 -- 附件JSON
    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (issue_id) REFERENCES acceptance_issues(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_follow_ups_issue ON issue_follow_ups(issue_id);

-- ============================================
-- 8. 验收签字记录表
-- ============================================

CREATE TABLE IF NOT EXISTS acceptance_signatures (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id            INTEGER NOT NULL,                     -- 验收单ID
    signer_type         VARCHAR(20) NOT NULL,                 -- QA/PM/CUSTOMER/WITNESS
    signer_role         VARCHAR(50),                          -- 签字人角色
    signer_name         VARCHAR(100) NOT NULL,                -- 签字人姓名
    signer_user_id      INTEGER,                              -- 系统用户ID
    signer_company      VARCHAR(200),                         -- 签字人公司
    signature_data      TEXT,                                 -- 电子签名数据
    signed_at           DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address          VARCHAR(50),                          -- 签字IP
    device_info         VARCHAR(200),                         -- 设备信息

    FOREIGN KEY (order_id) REFERENCES acceptance_orders(id),
    FOREIGN KEY (signer_user_id) REFERENCES users(id)
);

CREATE INDEX idx_signatures_order ON acceptance_signatures(order_id);

-- ============================================
-- 9. 验收报告表
-- ============================================

CREATE TABLE IF NOT EXISTS acceptance_reports (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id            INTEGER NOT NULL,                     -- 验收单ID
    report_no           VARCHAR(50) NOT NULL UNIQUE,          -- 报告编号
    report_type         VARCHAR(20) NOT NULL,                 -- DRAFT/OFFICIAL
    version             INTEGER DEFAULT 1,                    -- 版本号

    -- 报告内容
    report_content      TEXT,                                 -- 报告正文

    -- 文件信息
    file_path           VARCHAR(500),                         -- PDF文件路径
    file_size           INTEGER,                              -- 文件大小
    file_hash           VARCHAR(64),                          -- 文件哈希

    generated_at        DATETIME,                             -- 生成时间
    generated_by        INTEGER,                              -- 生成人

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (order_id) REFERENCES acceptance_orders(id),
    FOREIGN KEY (generated_by) REFERENCES users(id)
);

CREATE INDEX idx_reports_order ON acceptance_reports(order_id);

-- ============================================
-- 10. 视图定义
-- ============================================

-- 验收单概览视图
CREATE VIEW IF NOT EXISTS v_acceptance_overview AS
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

-- ============================================
-- 完成
-- ============================================
