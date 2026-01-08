-- ============================================
-- 项目模板版本管理
-- 创建日期: 2026-01-08
-- ============================================

-- 项目模板版本表
CREATE TABLE IF NOT EXISTS project_template_versions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id         INTEGER NOT NULL,                     -- 模板ID
    version_no          VARCHAR(20) NOT NULL,                 -- 版本号
    status              VARCHAR(20) DEFAULT 'DRAFT',          -- 状态：DRAFT/ACTIVE/ARCHIVED
    template_config     TEXT,                                 -- 模板配置JSON
    release_notes       TEXT,                                 -- 版本说明
    created_by          INTEGER,                              -- 创建人ID
    published_by        INTEGER,                              -- 发布人ID
    published_at        DATETIME,                              -- 发布时间
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES project_templates(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (published_by) REFERENCES users(id)
);

CREATE UNIQUE INDEX idx_project_template_version_unique ON project_template_versions(template_id, version_no);
CREATE INDEX idx_project_template_version_status ON project_template_versions(status);
CREATE INDEX idx_project_template_version_template ON project_template_versions(template_id);

-- 在项目模板表中添加当前版本ID字段
ALTER TABLE project_templates ADD COLUMN current_version_id INTEGER;
CREATE INDEX idx_project_template_current_version ON project_templates(current_version_id);





