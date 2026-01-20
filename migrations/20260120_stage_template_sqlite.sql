-- 阶段模板化功能 - SQLite 迁移脚本
-- 创建日期: 2026-01-20

-- 1. 阶段模板表
CREATE TABLE IF NOT EXISTS stage_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(50) NOT NULL UNIQUE,
    template_name VARCHAR(100) NOT NULL,
    description TEXT,
    project_type VARCHAR(20) DEFAULT 'CUSTOM',
    is_default INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. 大阶段定义表
CREATE TABLE IF NOT EXISTS stage_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL REFERENCES stage_templates(id) ON DELETE CASCADE,
    stage_code VARCHAR(20) NOT NULL,
    stage_name VARCHAR(100) NOT NULL,
    sequence INTEGER NOT NULL DEFAULT 0,
    estimated_days INTEGER,
    description TEXT,
    is_required INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. 小节点定义表
CREATE TABLE IF NOT EXISTS node_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_definition_id INTEGER NOT NULL REFERENCES stage_definitions(id) ON DELETE CASCADE,
    node_code VARCHAR(20) NOT NULL,
    node_name VARCHAR(100) NOT NULL,
    node_type VARCHAR(20) NOT NULL DEFAULT 'TASK',
    sequence INTEGER NOT NULL DEFAULT 0,
    estimated_days INTEGER,
    completion_method VARCHAR(20) NOT NULL DEFAULT 'MANUAL',
    dependency_node_ids TEXT,  -- JSON array
    is_required INTEGER DEFAULT 1,
    required_attachments INTEGER DEFAULT 0,
    approval_role_ids TEXT,  -- JSON array
    auto_condition TEXT,  -- JSON
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 4. 项目阶段实例表
CREATE TABLE IF NOT EXISTS project_stage_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    stage_definition_id INTEGER REFERENCES stage_definitions(id) ON DELETE SET NULL,
    stage_code VARCHAR(20) NOT NULL,
    stage_name VARCHAR(100) NOT NULL,
    sequence INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    is_modified INTEGER DEFAULT 0,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 5. 项目节点实例表
CREATE TABLE IF NOT EXISTS project_node_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    stage_instance_id INTEGER NOT NULL REFERENCES project_stage_instances(id) ON DELETE CASCADE,
    node_definition_id INTEGER REFERENCES node_definitions(id) ON DELETE SET NULL,
    node_code VARCHAR(20) NOT NULL,
    node_name VARCHAR(100) NOT NULL,
    node_type VARCHAR(20) NOT NULL DEFAULT 'TASK',
    sequence INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    completion_method VARCHAR(20) NOT NULL DEFAULT 'MANUAL',
    dependency_node_instance_ids TEXT,  -- JSON array
    is_required INTEGER DEFAULT 1,
    planned_date DATE,
    actual_date DATE,
    completed_by INTEGER REFERENCES users(id),
    completed_at DATETIME,
    attachments TEXT,  -- JSON array
    approval_record_id INTEGER,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 6. 为 projects 表添加阶段模板关联字段
ALTER TABLE projects ADD COLUMN stage_template_id INTEGER REFERENCES stage_templates(id);
ALTER TABLE projects ADD COLUMN current_stage_instance_id INTEGER;
ALTER TABLE projects ADD COLUMN current_node_instance_id INTEGER;

-- 7. 创建索引
CREATE INDEX IF NOT EXISTS idx_stage_definitions_template ON stage_definitions(template_id);
CREATE INDEX IF NOT EXISTS idx_node_definitions_stage ON node_definitions(stage_definition_id);
CREATE INDEX IF NOT EXISTS idx_project_stage_instances_project ON project_stage_instances(project_id);
CREATE INDEX IF NOT EXISTS idx_project_stage_instances_status ON project_stage_instances(status);
CREATE INDEX IF NOT EXISTS idx_project_node_instances_project ON project_node_instances(project_id);
CREATE INDEX IF NOT EXISTS idx_project_node_instances_stage ON project_node_instances(stage_instance_id);
CREATE INDEX IF NOT EXISTS idx_project_node_instances_status ON project_node_instances(status);
CREATE INDEX IF NOT EXISTS idx_projects_stage_template ON projects(stage_template_id);
