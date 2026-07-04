-- 售前智能体运行埋点表（M5 核心指标采集）
-- 每次智能体分析落一条记录，统计方案初稿周期/报价周期/使用次数/步骤成功率等 KPI
CREATE TABLE IF NOT EXISTS presale_agent_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    created_by INTEGER,
    requirement_text TEXT,
    industry VARCHAR(100),
    equipment_type VARCHAR(100),
    total_time DECIMAL(8, 2),
    solution_draft_time DECIMAL(8, 2),
    quote_time DECIMAL(8, 2),
    steps_ok JSON,
    cited_case_count INTEGER,
    quote_sample_count INTEGER,
    status VARCHAR(20),
    error TEXT,
    is_converted INTEGER,
    actual_project_id INTEGER,
    created_at DATETIME,
    updated_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_presale_agent_metric_created_at
    ON presale_agent_metrics(created_at);
CREATE INDEX IF NOT EXISTS idx_presale_agent_metric_created_by
    ON presale_agent_metrics(created_by);
CREATE INDEX IF NOT EXISTS idx_presale_agent_metric_equipment
    ON presale_agent_metrics(equipment_type);
