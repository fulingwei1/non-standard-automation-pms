-- 项目模板配置表
CREATE TABLE IF NOT EXISTS project_template_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_code VARCHAR(50) UNIQUE NOT NULL,
    config_name VARCHAR(100) NOT NULL,
    description TEXT,
    base_template_code VARCHAR(50) NOT NULL,
    config_json TEXT,
    is_active BOOLEAN DEFAULT 1,
    is_default BOOLEAN DEFAULT 0,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_config_base_template ON project_template_configs(base_template_code);
CREATE INDEX idx_config_active ON project_template_configs(is_active);

-- 阶段配置表
CREATE TABLE IF NOT EXISTS stage_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_id INTEGER NOT NULL,
    stage_code VARCHAR(20) NOT NULL,
    stage_name VARCHAR(100),
    sequence INTEGER DEFAULT 0,
    is_enabled BOOLEAN DEFAULT 1,
    is_required BOOLEAN DEFAULT 0,
    custom_description TEXT,
    custom_estimated_days INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (config_id) REFERENCES project_template_configs(id) ON DELETE CASCADE,
    UNIQUE(config_id, stage_code)
);

CREATE INDEX idx_stage_config ON stage_configs(config_id);
CREATE INDEX idx_stage_sequence ON stage_configs(sequence);

-- 节点配置表
CREATE TABLE IF NOT EXISTS node_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_config_id INTEGER NOT NULL,
    node_code VARCHAR(20) NOT NULL,
    node_name VARCHAR(100),
    sequence INTEGER DEFAULT 0,
    is_enabled BOOLEAN DEFAULT 1,
    is_required BOOLEAN DEFAULT 0,
    custom_owner_role_code VARCHAR(50),
    custom_estimated_days INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stage_config_id) REFERENCES stage_configs(id) ON DELETE CASCADE,
    UNIQUE(stage_config_id, node_code)
);

CREATE INDEX idx_node_stage ON node_configs(stage_config_id);
CREATE INDEX idx_node_sequence ON node_configs(sequence);

-- 插入默认配置（基于标准全流程）
INSERT INTO project_template_configs (config_code, config_name, description, base_template_code, is_active, is_default, created_by)
VALUES ('CFG_STANDARD_DEFAULT', '标准全流程（默认）', '标准全流程模板的默认配置，包含所有阶段和节点', 'TPL_STANDARD', 1, 1, 1);
