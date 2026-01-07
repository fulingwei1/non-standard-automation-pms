-- ============================================
-- 问题管理中心模块 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-05
-- 说明: 统一的问题管理中心，支持项目问题、任务问题、验收问题等
-- ============================================

-- ============================================
-- 1. 问题表
-- ============================================

CREATE TABLE IF NOT EXISTS issues (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_no            VARCHAR(50) NOT NULL UNIQUE,          -- 问题编号
    category            VARCHAR(20) NOT NULL,                 -- 问题分类
    project_id          INTEGER,                              -- 关联项目ID
    machine_id          INTEGER,                              -- 关联机台ID
    task_id             INTEGER,                              -- 关联任务ID
    acceptance_order_id INTEGER,                              -- 关联验收单ID
    related_issue_id    INTEGER,                              -- 关联问题ID（父子问题）
    
    -- 问题基本信息
    issue_type          VARCHAR(20) NOT NULL,                 -- 问题类型
    severity            VARCHAR(20) NOT NULL,                 -- 严重程度
    priority            VARCHAR(20) DEFAULT 'MEDIUM',          -- 优先级
    title               VARCHAR(200) NOT NULL,                -- 问题标题
    description         TEXT NOT NULL,                        -- 问题描述
    
    -- 提出人信息
    reporter_id         INTEGER NOT NULL,                     -- 提出人ID
    reporter_name       VARCHAR(50),                          -- 提出人姓名
    report_date         DATETIME NOT NULL,                    -- 提出时间
    
    -- 处理人信息
    assignee_id         INTEGER,                              -- 处理负责人ID
    assignee_name       VARCHAR(50),                          -- 处理负责人姓名
    due_date            DATE,                                 -- 要求完成日期
    
    -- 状态信息
    status              VARCHAR(20) DEFAULT 'OPEN' NOT NULL, -- 问题状态
    
    -- 解决信息
    solution            TEXT,                                 -- 解决方案
    resolved_at         DATETIME,                             -- 解决时间
    resolved_by         INTEGER,                              -- 解决人ID
    resolved_by_name    VARCHAR(50),                          -- 解决人姓名
    
    -- 验证信息
    verified_at         DATETIME,                             -- 验证时间
    verified_by         INTEGER,                              -- 验证人ID
    verified_by_name     VARCHAR(50),                          -- 验证人姓名
    verified_result      VARCHAR(20),                          -- 验证结果
    
    -- 影响评估
    impact_scope        TEXT,                                 -- 影响范围
    impact_level        VARCHAR(20),                          -- 影响级别
    is_blocking         BOOLEAN DEFAULT 0,                    -- 是否阻塞
    
    -- 附件和标签
    attachments         TEXT,                                 -- 附件列表JSON
    tags                TEXT,                                 -- 标签JSON数组
    
    -- 统计信息
    follow_up_count     INTEGER DEFAULT 0,                    -- 跟进次数
    last_follow_up_at   DATETIME,                             -- 最后跟进时间
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (acceptance_order_id) REFERENCES acceptance_orders(id),
    FOREIGN KEY (related_issue_id) REFERENCES issues(id),
    FOREIGN KEY (reporter_id) REFERENCES users(id),
    FOREIGN KEY (assignee_id) REFERENCES users(id),
    FOREIGN KEY (resolved_by) REFERENCES users(id),
    FOREIGN KEY (verified_by) REFERENCES users(id)
);

CREATE INDEX idx_issue_no ON issues(issue_no);
CREATE INDEX idx_issue_category ON issues(category);
CREATE INDEX idx_issue_project ON issues(project_id);
CREATE INDEX idx_issue_machine ON issues(machine_id);
CREATE INDEX idx_issue_task ON issues(task_id);
CREATE INDEX idx_issue_status ON issues(status);
CREATE INDEX idx_issue_severity ON issues(severity);
CREATE INDEX idx_issue_priority ON issues(priority);
CREATE INDEX idx_issue_assignee ON issues(assignee_id);
CREATE INDEX idx_issue_reporter ON issues(reporter_id);
CREATE INDEX idx_issue_blocking ON issues(is_blocking);
CREATE INDEX idx_issue_due_date ON issues(due_date);

-- ============================================
-- 2. 问题跟进记录表（通用）
-- ============================================

CREATE TABLE IF NOT EXISTS issue_follow_up_records (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id            INTEGER NOT NULL,                     -- 问题ID
    follow_up_type      VARCHAR(20) NOT NULL,                 -- 跟进类型
    content             TEXT NOT NULL,                        -- 跟进内容
    operator_id         INTEGER NOT NULL,                     -- 操作人ID
    operator_name       VARCHAR(50),                          -- 操作人姓名
    old_status          VARCHAR(20),                          -- 原状态
    new_status          VARCHAR(20),                          -- 新状态
    attachments         TEXT,                                 -- 附件列表JSON
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (issue_id) REFERENCES issues(id),
    FOREIGN KEY (operator_id) REFERENCES users(id)
);

CREATE INDEX idx_follow_up_issue ON issue_follow_up_records(issue_id);
CREATE INDEX idx_follow_up_type ON issue_follow_up_records(follow_up_type);
CREATE INDEX idx_follow_up_operator ON issue_follow_up_records(operator_id);
CREATE INDEX idx_follow_up_created ON issue_follow_up_records(created_at);

