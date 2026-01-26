-- migrations/20260121_resource_plan_sqlite.sql
-- 项目阶段资源计划表

-- 资源计划主表
CREATE TABLE IF NOT EXISTS project_stage_resource_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    stage_code VARCHAR(10) NOT NULL,
    staffing_need_id INTEGER REFERENCES mes_project_staffing_need(id),
    role_code VARCHAR(50) NOT NULL,
    role_name VARCHAR(100),
    headcount INTEGER DEFAULT 1,
    allocation_pct DECIMAL(5,2) DEFAULT 100,
    assigned_employee_id INTEGER REFERENCES users(id),
    assignment_status VARCHAR(20) DEFAULT 'PENDING',
    planned_start DATE,
    planned_end DATE,
    remark TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stage_plan_project ON project_stage_resource_plan(project_id);
CREATE INDEX IF NOT EXISTS idx_stage_plan_stage ON project_stage_resource_plan(stage_code);
CREATE INDEX IF NOT EXISTS idx_stage_plan_employee ON project_stage_resource_plan(assigned_employee_id);
CREATE INDEX IF NOT EXISTS idx_stage_plan_status ON project_stage_resource_plan(assignment_status);
CREATE INDEX IF NOT EXISTS idx_stage_plan_dates ON project_stage_resource_plan(planned_start, planned_end);

-- 资源冲突记录表
CREATE TABLE IF NOT EXISTS resource_conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES users(id),
    plan_a_id INTEGER NOT NULL REFERENCES project_stage_resource_plan(id),
    plan_b_id INTEGER NOT NULL REFERENCES project_stage_resource_plan(id),
    overlap_start DATE NOT NULL,
    overlap_end DATE NOT NULL,
    total_allocation DECIMAL(5,2),
    over_allocation DECIMAL(5,2),
    severity VARCHAR(10) DEFAULT 'LOW',
    is_resolved INTEGER DEFAULT 0,
    resolved_by INTEGER REFERENCES users(id),
    resolved_at DATE,
    resolution_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conflict_employee ON resource_conflicts(employee_id);
CREATE INDEX IF NOT EXISTS idx_conflict_resolved ON resource_conflicts(is_resolved);
CREATE INDEX IF NOT EXISTS idx_conflict_severity ON resource_conflicts(severity);
