-- AS-04: engineer scheduling conflict-detection fact table.
-- The audit sandbox copies data/app.db directly, so the runtime SQLite table
-- must have timestamp defaults compatible with direct sqlite inserts.

CREATE TABLE IF NOT EXISTS engineer_task_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_no VARCHAR(50) UNIQUE,
    engineer_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    machine_id INTEGER,
    task_type VARCHAR(50),
    task_description TEXT,
    estimated_hours FLOAT DEFAULT 0,
    actual_hours FLOAT DEFAULT 0,
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    status VARCHAR(20) DEFAULT 'PENDING',
    priority INTEGER DEFAULT 50,
    quality_score FLOAT,
    is_on_time BOOLEAN DEFAULT 1,
    has_rework BOOLEAN DEFAULT 0,
    has_conflict BOOLEAN DEFAULT 0,
    conflict_description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_task_assign_engineer
ON engineer_task_assignments(engineer_id);

CREATE INDEX IF NOT EXISTS idx_task_assign_project
ON engineer_task_assignments(project_id);

CREATE INDEX IF NOT EXISTS idx_task_assign_status
ON engineer_task_assignments(status);

CREATE INDEX IF NOT EXISTS idx_task_assign_dates
ON engineer_task_assignments(planned_start_date, planned_end_date);
