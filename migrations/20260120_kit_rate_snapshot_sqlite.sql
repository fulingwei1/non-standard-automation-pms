-- 齐套率历史快照表 (SQLite)
-- 用于记录项目/机台每日的齐套率状态，支持历史趋势分析

CREATE TABLE IF NOT EXISTS mes_kit_rate_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 快照对象
    project_id INTEGER NOT NULL REFERENCES projects(id),
    machine_id INTEGER REFERENCES machines(id),

    -- 快照时间
    snapshot_date DATE NOT NULL,
    snapshot_time DATETIME NOT NULL,

    -- 快照来源
    snapshot_type VARCHAR(20) NOT NULL DEFAULT 'DAILY',  -- DAILY/STAGE_CHANGE/MANUAL
    trigger_event VARCHAR(100),

    -- 齐套率数据
    kit_rate DECIMAL(5,2) NOT NULL DEFAULT 0,
    kit_status VARCHAR(20) NOT NULL DEFAULT 'shortage',  -- complete/partial/shortage

    -- 物料统计
    total_items INTEGER DEFAULT 0,
    fulfilled_items INTEGER DEFAULT 0,
    shortage_items INTEGER DEFAULT 0,
    in_transit_items INTEGER DEFAULT 0,

    -- 阻塞性物料统计
    blocking_total INTEGER DEFAULT 0,
    blocking_fulfilled INTEGER DEFAULT 0,
    blocking_kit_rate DECIMAL(5,2) DEFAULT 0,

    -- 金额统计
    total_amount DECIMAL(14,2) DEFAULT 0,
    shortage_amount DECIMAL(14,2) DEFAULT 0,

    -- 项目阶段信息
    project_stage VARCHAR(20),
    project_health VARCHAR(10),

    -- 分阶段齐套率
    stage_kit_rates TEXT
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_kit_snapshot_project_date ON mes_kit_rate_snapshot(project_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_kit_snapshot_machine_date ON mes_kit_rate_snapshot(machine_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_kit_snapshot_type ON mes_kit_rate_snapshot(snapshot_type);
CREATE INDEX IF NOT EXISTS idx_kit_snapshot_date ON mes_kit_rate_snapshot(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_kit_snapshot_project_time ON mes_kit_rate_snapshot(project_id, snapshot_time);
