-- ============================================================
-- 项目-变更单联动集成：project_change_impacts 表
-- 支持数据库：SQLite / MySQL / PostgreSQL
-- 日期：2026-03-27
-- ============================================================

CREATE TABLE IF NOT EXISTS project_change_impacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 双向关联
    ecn_id INTEGER NOT NULL REFERENCES ecn(id),
    ecn_no VARCHAR(50) NOT NULL,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    machine_id INTEGER REFERENCES machines(id),

    -- 评估阶段：项目状态快照
    project_stage_snapshot VARCHAR(20),
    project_progress_snapshot DECIMAL(5,2),

    -- 进度影响
    schedule_impact_days INTEGER DEFAULT 0,
    affected_milestones TEXT,  -- JSON

    -- 成本影响
    rework_cost DECIMAL(14,2) DEFAULT 0,
    scrap_cost DECIMAL(14,2) DEFAULT 0,
    additional_cost DECIMAL(14,2) DEFAULT 0,
    total_cost_impact DECIMAL(14,2) DEFAULT 0,
    cost_breakdown TEXT,  -- JSON

    -- 风险评估
    risk_level VARCHAR(20) DEFAULT 'LOW',
    risk_description TEXT,

    -- 综合影响报告
    impact_summary TEXT,
    impact_report TEXT,  -- JSON

    assessed_by INTEGER REFERENCES users(id),
    assessed_at DATETIME,

    -- 执行阶段
    milestones_updated BOOLEAN DEFAULT 0,
    milestone_update_detail TEXT,  -- JSON

    costs_recorded BOOLEAN DEFAULT 0,
    cost_record_ids TEXT,  -- JSON

    risk_created BOOLEAN DEFAULT 0,
    risk_record_id INTEGER,

    actual_delay_days INTEGER,
    actual_cost_impact DECIMAL(14,2),

    -- 状态
    status VARCHAR(20) DEFAULT 'ASSESSED',

    executed_by INTEGER REFERENCES users(id),
    executed_at DATETIME,

    remark TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_pci_ecn ON project_change_impacts(ecn_id);
CREATE INDEX IF NOT EXISTS idx_pci_project ON project_change_impacts(project_id);
CREATE INDEX IF NOT EXISTS idx_pci_ecn_project ON project_change_impacts(ecn_id, project_id);
CREATE INDEX IF NOT EXISTS idx_pci_status ON project_change_impacts(status);
CREATE INDEX IF NOT EXISTS idx_pci_risk_level ON project_change_impacts(risk_level);
