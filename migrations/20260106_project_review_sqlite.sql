-- ============================================
-- 项目复盘模块 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-06
-- 说明: 项目复盘报告、经验教训、最佳实践
-- 适用场景：项目结项后的复盘总结、经验沉淀、知识复用
-- ============================================

-- ============================================
-- 1. 项目复盘报告表
-- ============================================

CREATE TABLE IF NOT EXISTS project_reviews (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    review_no           VARCHAR(50) NOT NULL UNIQUE,              -- 复盘编号
    project_id          INTEGER NOT NULL,                         -- 项目ID
    project_code        VARCHAR(50) NOT NULL,                      -- 项目编号
    
    -- 复盘信息
    review_date         DATE NOT NULL,                             -- 复盘日期
    review_type         VARCHAR(20) DEFAULT 'POST_MORTEM',        -- 复盘类型：POST_MORTEM/MID_TERM/QUARTERLY
    
    -- 项目周期对比
    plan_duration       INTEGER,                                   -- 计划工期(天)
    actual_duration     INTEGER,                                   -- 实际工期(天)
    schedule_variance   INTEGER,                                   -- 进度偏差(天)
    
    -- 成本对比
    budget_amount       DECIMAL(12,2),                             -- 预算金额
    actual_cost         DECIMAL(12,2),                             -- 实际成本
    cost_variance       DECIMAL(12,2),                             -- 成本偏差
    
    -- 质量指标
    quality_issues      INTEGER DEFAULT 0,                         -- 质量问题数
    change_count        INTEGER DEFAULT 0,                         -- 变更次数
    customer_satisfaction INTEGER,                                  -- 客户满意度1-5
    
    -- 复盘内容
    success_factors     TEXT,                                       -- 成功因素
    problems            TEXT,                                       -- 问题与教训
    improvements        TEXT,                                       -- 改进建议
    best_practices      TEXT,                                       -- 最佳实践
    conclusion          TEXT,                                       -- 复盘结论
    
    -- 参与人
    reviewer_id         INTEGER NOT NULL,                          -- 复盘负责人ID
    reviewer_name       VARCHAR(50) NOT NULL,                       -- 复盘负责人
    participants        TEXT,                                       -- 参与人ID列表（JSON）
    participant_names   VARCHAR(500),                               -- 参与人姓名（逗号分隔）
    
    -- 附件
    attachment_ids      TEXT,                                       -- 附件ID列表（JSON）
    
    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT',              -- 状态：DRAFT/PUBLISHED/ARCHIVED
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
);

CREATE INDEX idx_project_review_project ON project_reviews(project_id);
CREATE INDEX idx_project_review_date ON project_reviews(review_date);
CREATE INDEX idx_project_review_status ON project_reviews(status);

-- ============================================
-- 2. 项目经验教训表
-- ============================================

CREATE TABLE IF NOT EXISTS project_lessons (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id           INTEGER NOT NULL,                          -- 复盘报告ID
    project_id          INTEGER NOT NULL,                          -- 项目ID
    
    -- 经验教训信息
    lesson_type         VARCHAR(20) NOT NULL,                      -- 类型：SUCCESS/FAILURE
    title               VARCHAR(200) NOT NULL,                      -- 标题
    description         TEXT NOT NULL,                             -- 问题/经验描述
    
    -- 根因分析
    root_cause          TEXT,                                       -- 根本原因
    impact              TEXT,                                       -- 影响范围
    
    -- 改进措施
    improvement_action  TEXT,                                       -- 改进措施
    responsible_person  VARCHAR(50),                                -- 责任人
    due_date            DATE,                                       -- 完成日期
    
    -- 分类标签
    category            VARCHAR(50),                                -- 分类：进度/成本/质量/沟通/技术/管理
    tags                TEXT,                                       -- 标签列表（JSON）
    
    -- 优先级
    priority            VARCHAR(10) DEFAULT 'MEDIUM',             -- 优先级：LOW/MEDIUM/HIGH
    
    -- 状态
    status              VARCHAR(20) DEFAULT 'OPEN',                -- 状态：OPEN/IN_PROGRESS/RESOLVED/CLOSED
    resolved_date       DATE,                                       -- 解决日期
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (review_id) REFERENCES project_reviews(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX idx_project_lesson_review ON project_lessons(review_id);
CREATE INDEX idx_project_lesson_project ON project_lessons(project_id);
CREATE INDEX idx_project_lesson_type ON project_lessons(lesson_type);
CREATE INDEX idx_project_lesson_status ON project_lessons(status);

-- ============================================
-- 3. 项目最佳实践表
-- ============================================

CREATE TABLE IF NOT EXISTS project_best_practices (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id                   INTEGER NOT NULL,                  -- 复盘报告ID
    project_id                  INTEGER NOT NULL,                  -- 项目ID
    
    -- 最佳实践信息
    title                       VARCHAR(200) NOT NULL,              -- 标题
    description                 TEXT NOT NULL,                      -- 实践描述
    context                     TEXT,                                -- 适用场景
    implementation              TEXT,                                -- 实施方法
    benefits                    TEXT,                                -- 带来的收益
    
    -- 分类标签
    category                    VARCHAR(50),                         -- 分类：流程/工具/技术/管理/沟通
    tags                        TEXT,                                -- 标签列表（JSON）
    
    -- 可复用性
    is_reusable                 BOOLEAN DEFAULT 1,                  -- 是否可复用
    applicable_project_types    TEXT,                                -- 适用项目类型列表（JSON）
    applicable_stages           TEXT,                                -- 适用阶段列表（JSON，S1-S9）
    
    -- 验证信息
    validation_status           VARCHAR(20) DEFAULT 'PENDING',     -- 验证状态：PENDING/VALIDATED/REJECTED
    validation_date             DATE,                               -- 验证日期
    validated_by                INTEGER,                             -- 验证人ID
    
    -- 复用统计
    reuse_count                 INTEGER DEFAULT 0,                  -- 复用次数
    last_reused_at              DATETIME,                           -- 最后复用时间
    
    -- 状态
    status                      VARCHAR(20) DEFAULT 'ACTIVE',       -- 状态：ACTIVE/ARCHIVED
    
    created_at                  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at                  DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (review_id) REFERENCES project_reviews(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (validated_by) REFERENCES users(id)
);

CREATE INDEX idx_project_bp_review ON project_best_practices(review_id);
CREATE INDEX idx_project_bp_project ON project_best_practices(project_id);
CREATE INDEX idx_project_bp_category ON project_best_practices(category);
CREATE INDEX idx_project_bp_reusable ON project_best_practices(is_reusable);
CREATE INDEX idx_project_bp_status ON project_best_practices(status);


