-- 售前智能体结果修订记录表（记录工程师对 AI 产出的修改，反哺 AI 改进）
CREATE TABLE IF NOT EXISTS presale_agent_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_id INTEGER,
    job_id INTEGER,
    requirement_text TEXT,
    ai_output JSON,
    revised_output JSON,
    fields_diff JSON,
    revised_by INTEGER,
    revised_by_name VARCHAR(100),
    revision_note TEXT,
    changed_field_count INTEGER DEFAULT 0,
    is_major_revision INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'CONFIRMED',
    created_at DATETIME,
    updated_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_presale_revision_metric ON presale_agent_revisions(metric_id);
CREATE INDEX IF NOT EXISTS idx_presale_revision_created ON presale_agent_revisions(created_at);
CREATE INDEX IF NOT EXISTS idx_presale_revision_by ON presale_agent_revisions(revised_by);
