-- AI 后台生成任务表（把重的 AI 生成改为后台任务+轮询）
CREATE TABLE IF NOT EXISTS ai_generation_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    params JSON,
    result JSON,
    error TEXT,
    progress INTEGER DEFAULT 0,
    created_by INTEGER,
    started_at DATETIME,
    finished_at DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ai_jobs_status ON ai_generation_jobs(status);
CREATE INDEX IF NOT EXISTS idx_ai_jobs_type ON ai_generation_jobs(job_type);
