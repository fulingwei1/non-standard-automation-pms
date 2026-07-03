-- AI 产出反馈表：记录人工对 AI 产出的采纳/驳回结论（结果反馈环节 0→1）。
-- append-only；同一产出多次反馈统计口径取最新一条。

CREATE TABLE IF NOT EXISTS ai_output_feedbacks (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    feature_key VARCHAR(60) NOT NULL,
    ref_type VARCHAR(50),
    ref_id INTEGER,
    verdict VARCHAR(20) NOT NULL,
    reason TEXT,
    detail JSON,
    created_by INTEGER,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE INDEX IF NOT EXISTS idx_ai_output_feedbacks_feature ON ai_output_feedbacks (feature_key);
CREATE INDEX IF NOT EXISTS idx_ai_output_feedbacks_ref ON ai_output_feedbacks (ref_id);
