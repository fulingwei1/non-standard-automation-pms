-- migrations/20260130_project_risk_tables_mysql.sql
-- 项目风险历史和快照表（MySQL版本）
-- 用于支持项目风险自动计算和趋势分析

START TRANSACTION;

-- =====================================================
-- 项目风险历史表
-- 记录项目风险等级的变更历史
-- =====================================================
CREATE TABLE IF NOT EXISTS project_risk_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,

    -- 风险等级变化
    old_risk_level VARCHAR(20) COMMENT '原风险等级: LOW/MEDIUM/HIGH/CRITICAL',
    new_risk_level VARCHAR(20) COMMENT '新风险等级: LOW/MEDIUM/HIGH/CRITICAL',

    -- 风险因子（JSON格式存储详细数据）
    risk_factors JSON COMMENT '风险因子详情',

    -- 触发信息
    triggered_by VARCHAR(50) DEFAULT 'SYSTEM' COMMENT '触发者：SYSTEM/MANUAL/用户ID',
    triggered_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '触发时间',

    -- 备注
    remarks TEXT COMMENT '备注说明',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- 外键
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,

    -- 索引
    INDEX idx_project_risk_history_project (project_id),
    INDEX idx_project_risk_history_triggered_at (triggered_at),
    INDEX idx_project_risk_history_level (new_risk_level),

    COMMENT '项目风险历史表'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =====================================================
-- 项目风险快照表
-- 定期保存项目的风险状态快照，用于趋势分析
-- =====================================================
CREATE TABLE IF NOT EXISTS project_risk_snapshot (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,

    -- 快照时间
    snapshot_date DATETIME NOT NULL COMMENT '快照日期',

    -- 风险等级
    risk_level VARCHAR(20) COMMENT '风险等级',

    -- 风险指标
    overdue_milestones_count INT DEFAULT 0 COMMENT '逾期里程碑数',
    total_milestones_count INT DEFAULT 0 COMMENT '总里程碑数',
    overdue_tasks_count INT DEFAULT 0 COMMENT '逾期任务数',
    open_risks_count INT DEFAULT 0 COMMENT '未关闭风险数',
    high_risks_count INT DEFAULT 0 COMMENT '高风险数',

    -- 详细数据
    risk_factors JSON COMMENT '风险因子详情',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- 外键
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,

    -- 索引
    INDEX idx_project_risk_snapshot_project (project_id),
    INDEX idx_project_risk_snapshot_date (snapshot_date),
    INDEX idx_project_risk_snapshot_level (risk_level),
    INDEX idx_project_risk_snapshot_project_date (project_id, snapshot_date),

    COMMENT '项目风险快照表'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =====================================================
-- 为projects表添加风险相关字段（如果不存在）
-- =====================================================

-- 添加 risk_level 列（如果不存在）
SET @column_exists = (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = DATABASE()
    AND table_name = 'projects'
    AND column_name = 'risk_level'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE projects ADD COLUMN risk_level VARCHAR(20) DEFAULT ''LOW'' COMMENT ''风险等级''',
    'SELECT ''Column risk_level already exists'''
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 risk_factors 列（如果不存在）
SET @column_exists = (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = DATABASE()
    AND table_name = 'projects'
    AND column_name = 'risk_factors'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE projects ADD COLUMN risk_factors JSON COMMENT ''风险因子详情''',
    'SELECT ''Column risk_factors already exists'''
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 risk_calculated_at 列（如果不存在）
SET @column_exists = (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = DATABASE()
    AND table_name = 'projects'
    AND column_name = 'risk_calculated_at'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE projects ADD COLUMN risk_calculated_at DATETIME COMMENT ''风险计算时间''',
    'SELECT ''Column risk_calculated_at already exists'''
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 创建索引（如果不存在）
CREATE INDEX IF NOT EXISTS idx_projects_risk_level ON projects(risk_level);

COMMIT;
