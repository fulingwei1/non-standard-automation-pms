-- ============================================================
-- 工作日志模块 DDL - SQLite 版本
-- 创建日期：2026-01-09
-- ============================================================

-- ==================== 工作日志 ====================

-- 工作日志表
CREATE TABLE IF NOT EXISTS work_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 人员信息
    user_id INTEGER NOT NULL,                    -- 提交人ID
    user_name VARCHAR(50),                       -- 提交人姓名（冗余字段）
    
    -- 工作信息
    work_date DATE NOT NULL,                     -- 工作日期
    content TEXT NOT NULL,                       -- 工作内容（限制300字）
    
    -- 状态
    status VARCHAR(20) DEFAULT 'DRAFT',          -- 状态：DRAFT/SUBMITTED
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_work_log_user ON work_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_work_log_date ON work_logs(work_date);
CREATE INDEX IF NOT EXISTS idx_work_log_status ON work_logs(status);
CREATE INDEX IF NOT EXISTS idx_work_log_user_date ON work_logs(user_id, work_date);
CREATE UNIQUE INDEX IF NOT EXISTS uq_work_log_user_date ON work_logs(user_id, work_date);

-- ==================== 工作日志配置 ====================

-- 工作日志配置表
CREATE TABLE IF NOT EXISTS work_log_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 适用范围
    user_id INTEGER,                             -- 用户ID（NULL表示全员）
    department_id INTEGER,                       -- 部门ID（可选）
    
    -- 配置项
    is_required INTEGER DEFAULT 1,               -- 是否必须提交
    is_active INTEGER DEFAULT 1,                 -- 是否启用
    remind_time VARCHAR(10) DEFAULT '18:00',     -- 提醒时间（HH:mm格式）
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_work_log_config_user ON work_log_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_work_log_config_dept ON work_log_configs(department_id);
CREATE INDEX IF NOT EXISTS idx_work_log_config_active ON work_log_configs(is_active);

-- ==================== 工作日志提及关联 ====================

-- 工作日志提及关联表
CREATE TABLE IF NOT EXISTS work_log_mentions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 关联工作日志
    work_log_id INTEGER NOT NULL,                -- 工作日志ID
    
    -- 提及信息
    mention_type VARCHAR(20) NOT NULL,           -- 提及类型：PROJECT/MACHINE/USER
    mention_id INTEGER NOT NULL,                  -- 被提及对象ID
    mention_name VARCHAR(200),                   -- 被提及对象名称（冗余字段）
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (work_log_id) REFERENCES work_logs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_work_log_mention_log ON work_log_mentions(work_log_id);
CREATE INDEX IF NOT EXISTS idx_work_log_mention_type ON work_log_mentions(mention_type);
CREATE INDEX IF NOT EXISTS idx_work_log_mention_id ON work_log_mentions(mention_id);
CREATE INDEX IF NOT EXISTS idx_work_log_mention_type_id ON work_log_mentions(mention_type, mention_id);
