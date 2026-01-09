-- Progress tracking module migration (SQLite)
-- Targets: WBS templates, tasks, dependencies, progress logs, baselines

-- PRAGMA foreign_keys = ON;  -- Disabled for migration
BEGIN;

-- WBS templates
CREATE TABLE IF NOT EXISTS wbs_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(20) UNIQUE NOT NULL,
    template_name VARCHAR(100) NOT NULL,
    project_type VARCHAR(20),
    equipment_type VARCHAR(20),
    version_no VARCHAR(10) DEFAULT 'V1',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- WBS template tasks
CREATE TABLE IF NOT EXISTS wbs_template_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    task_name VARCHAR(200),
    stage VARCHAR(20),
    default_owner_role VARCHAR(50),
    plan_days INTEGER,
    weight DECIMAL(5,2) DEFAULT 1,
    depends_on_template_task_id INTEGER,
    FOREIGN KEY (template_id) REFERENCES wbs_templates(id),
    FOREIGN KEY (depends_on_template_task_id) REFERENCES wbs_template_tasks(id)
);

-- Project tasks
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    machine_id INTEGER,
    milestone_id INTEGER,
    task_name VARCHAR(200) NOT NULL,
    stage VARCHAR(20),
    status VARCHAR(20) DEFAULT 'TODO',
    owner_id INTEGER,
    plan_start DATE,
    plan_end DATE,
    actual_start DATE,
    actual_end DATE,
    progress_percent INTEGER DEFAULT 0,
    weight DECIMAL(5,2) DEFAULT 1,
    block_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (milestone_id) REFERENCES milestones(id),
    FOREIGN KEY (owner_id) REFERENCES employees(id)
);

-- Task dependencies
CREATE TABLE IF NOT EXISTS task_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    depends_on_task_id INTEGER NOT NULL,
    dependency_type VARCHAR(10) DEFAULT 'FS',
    lag_days INTEGER DEFAULT 0,
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id)
);

-- Progress logs
CREATE TABLE IF NOT EXISTS progress_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    progress_percent INTEGER,
    update_note TEXT,
    updated_by INTEGER,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (updated_by) REFERENCES employees(id)
);

-- Schedule baselines
CREATE TABLE IF NOT EXISTS schedule_baselines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    baseline_no VARCHAR(10) DEFAULT 'V1',
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (created_by) REFERENCES employees(id)
);

-- Baseline task snapshot
CREATE TABLE IF NOT EXISTS baseline_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    baseline_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    plan_start DATE,
    plan_end DATE,
    weight DECIMAL(5,2),
    FOREIGN KEY (baseline_id) REFERENCES schedule_baselines(id),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_wbs_template_tasks_template ON wbs_template_tasks(template_id);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_milestone ON tasks(milestone_id);
CREATE INDEX IF NOT EXISTS idx_tasks_owner ON tasks(owner_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_task_deps_task ON task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_task_deps_depends ON task_dependencies(depends_on_task_id);
CREATE INDEX IF NOT EXISTS idx_progress_logs_task ON progress_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_schedule_baselines_project ON schedule_baselines(project_id);
CREATE INDEX IF NOT EXISTS idx_baseline_tasks_baseline ON baseline_tasks(baseline_id);

COMMIT;
