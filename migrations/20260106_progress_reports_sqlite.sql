-- Progress reports table migration (SQLite)
-- Add progress_reports table for daily/weekly progress reports

-- PRAGMA foreign_keys = ON;  -- Disabled for migration
BEGIN;

-- Progress reports table
CREATE TABLE IF NOT EXISTS progress_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_type VARCHAR(20) NOT NULL,
    report_date DATE NOT NULL,
    
    -- 关联信息（三选一或组合）
    project_id INTEGER,
    machine_id INTEGER,
    task_id INTEGER,
    
    -- 报告内容
    content TEXT NOT NULL,
    completed_work TEXT,
    planned_work TEXT,
    issues TEXT,
    next_plan TEXT,
    
    -- 创建人
    created_by INTEGER NOT NULL,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_progress_reports_project ON progress_reports(project_id);
CREATE INDEX IF NOT EXISTS idx_progress_reports_machine ON progress_reports(machine_id);
CREATE INDEX IF NOT EXISTS idx_progress_reports_task ON progress_reports(task_id);
CREATE INDEX IF NOT EXISTS idx_progress_reports_date ON progress_reports(report_date);
CREATE INDEX IF NOT EXISTS idx_progress_reports_type ON progress_reports(report_type);

COMMIT;


