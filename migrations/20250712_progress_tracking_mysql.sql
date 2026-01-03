-- Progress tracking module migration (MySQL 8+)
-- Targets: WBS templates, tasks, dependencies, progress logs, baselines

-- WBS templates
CREATE TABLE IF NOT EXISTS wbs_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_code VARCHAR(20) UNIQUE NOT NULL,
    template_name VARCHAR(100) NOT NULL,
    project_type VARCHAR(20),
    equipment_type VARCHAR(20),
    version_no VARCHAR(10) DEFAULT 'V1',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- WBS template tasks
CREATE TABLE IF NOT EXISTS wbs_template_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_id INT NOT NULL,
    task_name VARCHAR(200),
    stage VARCHAR(20),
    default_owner_role VARCHAR(50),
    plan_days INT,
    weight DECIMAL(5,2) DEFAULT 1,
    depends_on_template_task_id INT,
    INDEX idx_wbs_template_tasks_template (template_id),
    CONSTRAINT fk_wbs_template_tasks_template FOREIGN KEY (template_id) REFERENCES wbs_templates(id),
    CONSTRAINT fk_wbs_template_tasks_dep FOREIGN KEY (depends_on_template_task_id) REFERENCES wbs_template_tasks(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Project tasks
CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    machine_id INT,
    milestone_id INT,
    task_name VARCHAR(200) NOT NULL,
    stage VARCHAR(20),
    status VARCHAR(20) DEFAULT 'TODO',
    owner_id INT,
    plan_start DATE,
    plan_end DATE,
    actual_start DATE,
    actual_end DATE,
    progress_percent INT DEFAULT 0,
    weight DECIMAL(5,2) DEFAULT 1,
    block_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tasks_project (project_id),
    INDEX idx_tasks_milestone (milestone_id),
    INDEX idx_tasks_owner (owner_id),
    INDEX idx_tasks_status (status),
    CONSTRAINT fk_tasks_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT fk_tasks_machine FOREIGN KEY (machine_id) REFERENCES machines(id),
    CONSTRAINT fk_tasks_milestone FOREIGN KEY (milestone_id) REFERENCES milestones(id),
    CONSTRAINT fk_tasks_owner FOREIGN KEY (owner_id) REFERENCES employees(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Task dependencies
CREATE TABLE IF NOT EXISTS task_dependencies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    depends_on_task_id INT NOT NULL,
    dependency_type VARCHAR(10) DEFAULT 'FS',
    lag_days INT DEFAULT 0,
    INDEX idx_task_deps_task (task_id),
    INDEX idx_task_deps_depends (depends_on_task_id),
    CONSTRAINT fk_task_deps_task FOREIGN KEY (task_id) REFERENCES tasks(id),
    CONSTRAINT fk_task_deps_depends FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Progress logs
CREATE TABLE IF NOT EXISTS progress_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    progress_percent INT,
    update_note TEXT,
    updated_by INT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_progress_logs_task (task_id),
    CONSTRAINT fk_progress_logs_task FOREIGN KEY (task_id) REFERENCES tasks(id),
    CONSTRAINT fk_progress_logs_updated_by FOREIGN KEY (updated_by) REFERENCES employees(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Schedule baselines
CREATE TABLE IF NOT EXISTS schedule_baselines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    baseline_no VARCHAR(10) DEFAULT 'V1',
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_schedule_baselines_project (project_id),
    CONSTRAINT fk_schedule_baselines_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT fk_schedule_baselines_created_by FOREIGN KEY (created_by) REFERENCES employees(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Baseline task snapshot
CREATE TABLE IF NOT EXISTS baseline_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    baseline_id INT NOT NULL,
    task_id INT NOT NULL,
    plan_start DATE,
    plan_end DATE,
    weight DECIMAL(5,2),
    INDEX idx_baseline_tasks_baseline (baseline_id),
    CONSTRAINT fk_baseline_tasks_baseline FOREIGN KEY (baseline_id) REFERENCES schedule_baselines(id),
    CONSTRAINT fk_baseline_tasks_task FOREIGN KEY (task_id) REFERENCES tasks(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
