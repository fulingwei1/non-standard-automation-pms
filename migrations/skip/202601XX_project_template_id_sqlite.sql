-- 添加项目模板关联字段（Sprint 4.1: 项目模板使用统计）
-- 创建日期: 2025-01-XX

-- SQLite 版本

-- 添加 template_id 字段
ALTER TABLE projects ADD COLUMN template_id INTEGER REFERENCES project_templates(id);

-- 添加 template_version_id 字段
ALTER TABLE projects ADD COLUMN template_version_id INTEGER REFERENCES project_template_versions(id);

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_projects_template_id ON projects(template_id);
CREATE INDEX IF NOT EXISTS idx_projects_template_version_id ON projects(template_version_id);
