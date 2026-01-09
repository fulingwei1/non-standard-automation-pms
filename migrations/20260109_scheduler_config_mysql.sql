-- ============================================
-- 定时服务配置管理模块 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-09
-- 说明: 定时任务配置表，允许管理员配置任务执行频率和启用状态
-- ============================================

-- ============================================
-- 定时任务配置表
-- ============================================

CREATE TABLE IF NOT EXISTS scheduler_task_configs (
    id                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    task_id             VARCHAR(100) NOT NULL UNIQUE COMMENT '任务ID（对应scheduler_config.py中的id）',
    
    -- 任务基本信息（从scheduler_config.py同步，用于显示）
    task_name           VARCHAR(200) NOT NULL COMMENT '任务名称',
    module              VARCHAR(200) NOT NULL COMMENT '模块路径',
    callable_name       VARCHAR(100) NOT NULL COMMENT '函数名',
    owner               VARCHAR(100) COMMENT '负责人',
    category            VARCHAR(100) COMMENT '分类',
    description         TEXT COMMENT '描述',
    
    -- 配置信息（可修改）
    is_enabled          BOOLEAN DEFAULT TRUE NOT NULL COMMENT '是否启用',
    cron_config         JSON NOT NULL COMMENT 'Cron配置（JSON格式：{"hour": 7, "minute": 0}）',
    
    -- 元数据（从scheduler_config.py同步，只读）
    dependencies_tables JSON COMMENT '依赖的数据库表列表',
    risk_level          VARCHAR(20) COMMENT '风险级别：LOW/MEDIUM/HIGH/CRITICAL',
    sla_config          JSON COMMENT 'SLA配置（最大执行时间、重试策略等）',
    
    -- 操作信息
    updated_by          INT UNSIGNED COMMENT '最后更新人ID',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_task_id (task_id),
    KEY idx_scheduler_task_id (task_id),
    KEY idx_scheduler_enabled (is_enabled),
    KEY idx_scheduler_category (category),
    FOREIGN KEY (updated_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='定时任务配置表';
