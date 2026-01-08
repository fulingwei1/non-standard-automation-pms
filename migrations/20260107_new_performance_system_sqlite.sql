-- ==========================================
-- 新绩效系统数据库迁移 - SQLite版本
-- 创建日期: 2026-01-07
-- 说明: 员工中心化绩效管理系统（月度总结+双评价）
-- ==========================================

-- ========== 1. 月度工作总结表 ==========

CREATE TABLE IF NOT EXISTS monthly_work_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    period VARCHAR(7) NOT NULL, -- 格式: YYYY-MM

    -- 工作总结内容（必填）
    work_content TEXT NOT NULL,
    self_evaluation TEXT NOT NULL,

    -- 工作总结内容（选填）
    highlights TEXT,
    problems TEXT,
    next_month_plan TEXT,

    -- 状态
    status VARCHAR(20) DEFAULT 'DRAFT', -- DRAFT/SUBMITTED/EVALUATING/COMPLETED

    -- 提交时间
    submit_date DATETIME,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    FOREIGN KEY (employee_id) REFERENCES users(id),

    -- 唯一约束
    UNIQUE (employee_id, period)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_monthly_summary_employee ON monthly_work_summary(employee_id);
CREATE INDEX IF NOT EXISTS idx_monthly_summary_period ON monthly_work_summary(period);
CREATE INDEX IF NOT EXISTS idx_monthly_summary_status ON monthly_work_summary(status);

-- ========== 2. 绩效评价记录表 ==========

CREATE TABLE IF NOT EXISTS performance_evaluation_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_id INTEGER NOT NULL,
    evaluator_id INTEGER NOT NULL,
    evaluator_type VARCHAR(20) NOT NULL, -- DEPT_MANAGER/PROJECT_MANAGER

    -- 项目信息（仅项目经理评价时使用）
    project_id INTEGER,
    project_weight INTEGER, -- 项目权重 (多项目时使用)

    -- 评价内容
    score INTEGER NOT NULL CHECK (score >= 60 AND score <= 100),
    comment TEXT NOT NULL,

    -- 状态
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING/COMPLETED
    evaluated_at DATETIME,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    FOREIGN KEY (summary_id) REFERENCES monthly_work_summary(id),
    FOREIGN KEY (evaluator_id) REFERENCES users(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_eval_record_summary ON performance_evaluation_record(summary_id);
CREATE INDEX IF NOT EXISTS idx_eval_record_evaluator ON performance_evaluation_record(evaluator_id);
CREATE INDEX IF NOT EXISTS idx_eval_record_project ON performance_evaluation_record(project_id);
CREATE INDEX IF NOT EXISTS idx_eval_record_status ON performance_evaluation_record(status);

-- ========== 3. 评价权重配置表 ==========

CREATE TABLE IF NOT EXISTS evaluation_weight_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_manager_weight INTEGER NOT NULL DEFAULT 50 CHECK (dept_manager_weight >= 0 AND dept_manager_weight <= 100),
    project_manager_weight INTEGER NOT NULL DEFAULT 50 CHECK (project_manager_weight >= 0 AND project_manager_weight <= 100),
    effective_date DATE NOT NULL,
    operator_id INTEGER NOT NULL,
    reason TEXT,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    FOREIGN KEY (operator_id) REFERENCES users(id),

    -- 权重总和必须为100（由应用层验证）
    CHECK (dept_manager_weight + project_manager_weight = 100)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_weight_config_effective_date ON evaluation_weight_config(effective_date);

-- ========== 初始数据 ==========

-- 插入默认权重配置（如果不存在）
INSERT OR IGNORE INTO evaluation_weight_config (
    dept_manager_weight,
    project_manager_weight,
    effective_date,
    operator_id,
    reason
) VALUES (
    50,
    50,
    DATE('now'),
    1, -- 假设admin用户ID为1
    '系统初始化默认配置'
);

-- ========== 完成 ==========
-- 迁移完成时间: 2026-01-07
