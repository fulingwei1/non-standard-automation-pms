-- Progress reports table migration (SQLite)
-- Add progress_reports table for daily/weekly progress reports

PRAGMA foreign_keys = ON;
BEGIN;

-- Progress reports table
CREATE TABLE IF NOT EXISTS progress_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_type VARCHAR(20) NOT NULL COMMENT '报告类型：daily/weekly',
    report_date DATE NOT NULL COMMENT '报告日期',
    
    -- 关联信息（三选一或组合）
    project_id INTEGER COMMENT '项目ID',
    machine_id INTEGER COMMENT '机台ID',
    task_id INTEGER COMMENT '任务ID',
    
    -- 报告内容
    content TEXT NOT NULL COMMENT '报告内容',
    completed_work TEXT COMMENT '已完成工作',
    planned_work TEXT COMMENT '计划工作',
    issues TEXT COMMENT '问题与阻塞',
    next_plan TEXT COMMENT '下一步计划',
    
    -- 创建人
    created_by INTEGER NOT NULL COMMENT '创建人ID',
    
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


