-- ============================================
-- 定时服务配置管理模块 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-09
-- 说明: 定时任务配置表，允许管理员配置任务执行频率和启用状态
-- ============================================

-- ============================================
-- 定时任务配置表
-- ============================================

CREATE TABLE IF NOT EXISTS scheduler_task_configs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id             VARCHAR(100) NOT NULL UNIQUE,            -- 任务ID（对应scheduler_config.py中的id）
    
    -- 任务基本信息（从scheduler_config.py同步，用于显示）
    task_name           VARCHAR(200) NOT NULL,                    -- 任务名称
    module              VARCHAR(200) NOT NULL,                    -- 模块路径
    callable_name       VARCHAR(100) NOT NULL,                    -- 函数名
    owner               VARCHAR(100),                             -- 负责人
    category            VARCHAR(100),                             -- 分类
    description         TEXT,                                      -- 描述
    
    -- 配置信息（可修改）
    is_enabled          BOOLEAN DEFAULT 1 NOT NULL,               -- 是否启用
    cron_config         TEXT NOT NULL,                            -- Cron配置（JSON格式，存储为TEXT）
    
    -- 元数据（从scheduler_config.py同步，只读）
    dependencies_tables TEXT,                                     -- 依赖的数据库表列表（JSON格式，存储为TEXT）
    risk_level          VARCHAR(20),                              -- 风险级别：LOW/MEDIUM/HIGH/CRITICAL
    sla_config          TEXT,                                     -- SLA配置（JSON格式，存储为TEXT）
    
    -- 操作信息
    updated_by          INTEGER,                                  -- 最后更新人ID
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,      -- 创建时间
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,      -- 更新时间
    
    FOREIGN KEY (updated_by) REFERENCES users(id)
);

CREATE INDEX idx_scheduler_task_id ON scheduler_task_configs(task_id);
CREATE INDEX idx_scheduler_enabled ON scheduler_task_configs(is_enabled);
CREATE INDEX idx_scheduler_category ON scheduler_task_configs(category);
