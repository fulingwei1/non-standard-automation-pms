-- 添加项目模板关联字段（Sprint 4.1: 项目模板使用统计）
-- 创建日期: 2025-01-XX

-- MySQL 版本

-- 添加 template_id 字段
ALTER TABLE projects 
ADD COLUMN template_id INT NULL COMMENT '创建时使用的模板ID' AFTER is_archived,
ADD CONSTRAINT fk_projects_template FOREIGN KEY (template_id) REFERENCES project_templates(id) ON DELETE SET NULL;

-- 添加 template_version_id 字段
ALTER TABLE projects 
ADD COLUMN template_version_id INT NULL COMMENT '创建时使用的模板版本ID' AFTER template_id,
ADD CONSTRAINT fk_projects_template_version FOREIGN KEY (template_version_id) REFERENCES project_template_versions(id) ON DELETE SET NULL;

-- 添加索引
CREATE INDEX idx_projects_template_id ON projects(template_id);
CREATE INDEX idx_projects_template_version_id ON projects(template_version_id);
