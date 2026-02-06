-- migrations/20260130_project_risk_tables_sqlite.sql
-- 项目风险历史和快照表（SQLite版本）
-- 用于支持项目风险自动计算和趋势分析

-- =====================================================
-- 项目风险历史表
-- 记录项目风险等级的变更历史
-- =====================================================
CREATE TABLE IF NOT EXISTS project_risk_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),

    -- 风险等级变化
    old_risk_level VARCHAR(20),  -- 原风险等级: LOW/MEDIUM/HIGH/CRITICAL
    new_risk_level VARCHAR(20),  -- 新风险等级: LOW/MEDIUM/HIGH/CRITICAL

    -- 风险因子（JSON格式存储详细数据）
    risk_factors JSON,  -- 风险因子详情

    -- 触发信息
    triggered_by VARCHAR(50) DEFAULT 'SYSTEM',  -- 触发者：SYSTEM/MANUAL/用户ID
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 触发时间

    -- 备注
    remarks TEXT,  -- 备注说明

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_project_risk_history_project ON project_risk_history(project_id);
CREATE INDEX IF NOT EXISTS idx_project_risk_history_triggered_at ON project_risk_history(triggered_at);
CREATE INDEX IF NOT EXISTS idx_project_risk_history_level ON project_risk_history(new_risk_level);

-- =====================================================
-- 项目风险快照表
-- 定期保存项目的风险状态快照，用于趋势分析
-- =====================================================
CREATE TABLE IF NOT EXISTS project_risk_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),

    -- 快照时间
    snapshot_date TIMESTAMP NOT NULL,  -- 快照日期

    -- 风险等级
    risk_level VARCHAR(20),  -- 风险等级

    -- 风险指标
    overdue_milestones_count INTEGER DEFAULT 0,  -- 逾期里程碑数
    total_milestones_count INTEGER DEFAULT 0,  -- 总里程碑数
    overdue_tasks_count INTEGER DEFAULT 0,  -- 逾期任务数
    open_risks_count INTEGER DEFAULT 0,  -- 未关闭风险数
    high_risks_count INTEGER DEFAULT 0,  -- 高风险数

    -- 详细数据
    risk_factors JSON,  -- 风险因子详情

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_project_risk_snapshot_project ON project_risk_snapshot(project_id);
CREATE INDEX IF NOT EXISTS idx_project_risk_snapshot_date ON project_risk_snapshot(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_project_risk_snapshot_level ON project_risk_snapshot(risk_level);
