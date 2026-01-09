-- ============================================
-- 项目模板表
-- 创建日期: 2026-01-07
-- ============================================

-- 项目模板表
CREATE TABLE IF NOT EXISTS project_templates (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code       VARCHAR(50) NOT NULL UNIQUE,              -- 模板编号
    template_name       VARCHAR(200) NOT NULL,                    -- 模板名称
    template_type       VARCHAR(20) DEFAULT 'STANDARD',           -- 模板类型：STANDARD/CUSTOM
    description         TEXT,                                     -- 模板描述
    stages_config       TEXT,                                     -- 阶段配置JSON
    milestones_config   TEXT,                                     -- 里程碑配置JSON
    default_members     TEXT,                                     -- 默认成员配置JSON
    is_active           INTEGER DEFAULT 1,                        -- 是否启用
    created_by          INTEGER,                                  -- 创建人ID
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_project_templates_code ON project_templates(template_code);
CREATE INDEX IF NOT EXISTS idx_project_templates_type ON project_templates(template_type);
CREATE INDEX IF NOT EXISTS idx_project_templates_active ON project_templates(is_active);
