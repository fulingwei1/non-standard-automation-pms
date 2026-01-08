-- ============================================
-- 项目模板版本管理
-- 创建日期: 2026-01-08
-- ============================================

-- 项目模板版本表
CREATE TABLE IF NOT EXISTS project_template_versions (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT,
    template_id         BIGINT NOT NULL COMMENT '模板ID',
    version_no          VARCHAR(20) NOT NULL COMMENT '版本号',
    status              VARCHAR(20) DEFAULT 'DRAFT' COMMENT '状态：DRAFT/ACTIVE/ARCHIVED',
    template_config     JSON COMMENT '模板配置JSON',
    release_notes       TEXT COMMENT '版本说明',
    created_by          BIGINT COMMENT '创建人ID',
    published_by        BIGINT COMMENT '发布人ID',
    published_at        DATETIME COMMENT '发布时间',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_template_version_template FOREIGN KEY (template_id) REFERENCES project_templates(id) ON DELETE CASCADE,
    CONSTRAINT fk_template_version_creator FOREIGN KEY (created_by) REFERENCES users(id),
    CONSTRAINT fk_template_version_publisher FOREIGN KEY (published_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目模板版本表';

CREATE UNIQUE INDEX idx_project_template_version_unique ON project_template_versions(template_id, version_no);
CREATE INDEX idx_project_template_version_status ON project_template_versions(status);
CREATE INDEX idx_project_template_version_template ON project_template_versions(template_id);

-- 在项目模板表中添加当前版本ID字段
ALTER TABLE project_templates ADD COLUMN current_version_id BIGINT COMMENT '当前版本ID';
ALTER TABLE project_templates ADD CONSTRAINT fk_template_current_version FOREIGN KEY (current_version_id) REFERENCES project_template_versions(id);
CREATE INDEX idx_project_template_current_version ON project_templates(current_version_id);





