-- 阶段模板化功能 - MySQL 迁移脚本
-- 创建日期: 2026-01-20

-- 1. 阶段模板表
CREATE TABLE IF NOT EXISTS stage_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_code VARCHAR(50) NOT NULL UNIQUE COMMENT '模板编码',
    template_name VARCHAR(100) NOT NULL COMMENT '模板名称',
    description TEXT COMMENT '模板描述',
    project_type VARCHAR(20) DEFAULT 'CUSTOM' COMMENT '适用项目类型: NEW/REPEAT/SIMPLE/CUSTOM',
    is_default TINYINT(1) DEFAULT 0 COMMENT '是否默认模板',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    created_by INT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_stage_templates_created_by FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='阶段模板表';

-- 2. 大阶段定义表
CREATE TABLE IF NOT EXISTS stage_definitions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_id INT NOT NULL COMMENT '所属模板ID',
    stage_code VARCHAR(20) NOT NULL COMMENT '阶段编码',
    stage_name VARCHAR(100) NOT NULL COMMENT '阶段名称',
    sequence INT NOT NULL DEFAULT 0 COMMENT '排序序号',
    estimated_days INT COMMENT '预计工期(天)',
    description TEXT COMMENT '阶段描述',
    is_required TINYINT(1) DEFAULT 1 COMMENT '是否必需阶段',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_stage_definitions_template FOREIGN KEY (template_id) REFERENCES stage_templates(id) ON DELETE CASCADE,
    INDEX idx_stage_definitions_template (template_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='大阶段定义表';

-- 3. 小节点定义表
CREATE TABLE IF NOT EXISTS node_definitions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stage_definition_id INT NOT NULL COMMENT '所属阶段ID',
    node_code VARCHAR(20) NOT NULL COMMENT '节点编码',
    node_name VARCHAR(100) NOT NULL COMMENT '节点名称',
    node_type VARCHAR(20) NOT NULL DEFAULT 'TASK' COMMENT '节点类型: TASK/APPROVAL/DELIVERABLE',
    sequence INT NOT NULL DEFAULT 0 COMMENT '排序序号',
    estimated_days INT COMMENT '预计工期(天)',
    completion_method VARCHAR(20) NOT NULL DEFAULT 'MANUAL' COMMENT '完成方式: MANUAL/APPROVAL/UPLOAD/AUTO',
    dependency_node_ids JSON COMMENT '前置依赖节点ID列表',
    is_required TINYINT(1) DEFAULT 1 COMMENT '是否必需节点',
    required_attachments TINYINT(1) DEFAULT 0 COMMENT '是否需上传附件',
    approval_role_ids JSON COMMENT '审批角色ID列表',
    auto_condition JSON COMMENT '自动完成条件配置',
    description TEXT COMMENT '节点描述',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_node_definitions_stage FOREIGN KEY (stage_definition_id) REFERENCES stage_definitions(id) ON DELETE CASCADE,
    INDEX idx_node_definitions_stage (stage_definition_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='小节点定义表';

-- 4. 项目阶段实例表
CREATE TABLE IF NOT EXISTS project_stage_instances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL COMMENT '所属项目ID',
    stage_definition_id INT COMMENT '来源阶段定义ID',
    stage_code VARCHAR(20) NOT NULL COMMENT '阶段编码',
    stage_name VARCHAR(100) NOT NULL COMMENT '阶段名称',
    sequence INT NOT NULL DEFAULT 0 COMMENT '排序序号',
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '状态: PENDING/IN_PROGRESS/COMPLETED/SKIPPED',
    planned_start_date DATE COMMENT '计划开始日期',
    planned_end_date DATE COMMENT '计划结束日期',
    actual_start_date DATE COMMENT '实际开始日期',
    actual_end_date DATE COMMENT '实际结束日期',
    is_modified TINYINT(1) DEFAULT 0 COMMENT '是否被调整过',
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_project_stage_instances_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_project_stage_instances_definition FOREIGN KEY (stage_definition_id) REFERENCES stage_definitions(id) ON DELETE SET NULL,
    INDEX idx_project_stage_instances_project (project_id),
    INDEX idx_project_stage_instances_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目阶段实例表';

-- 5. 项目节点实例表
CREATE TABLE IF NOT EXISTS project_node_instances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL COMMENT '所属项目ID',
    stage_instance_id INT NOT NULL COMMENT '所属阶段实例ID',
    node_definition_id INT COMMENT '来源节点定义ID',
    node_code VARCHAR(20) NOT NULL COMMENT '节点编码',
    node_name VARCHAR(100) NOT NULL COMMENT '节点名称',
    node_type VARCHAR(20) NOT NULL DEFAULT 'TASK' COMMENT '节点类型',
    sequence INT NOT NULL DEFAULT 0 COMMENT '排序序号',
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '状态: PENDING/IN_PROGRESS/COMPLETED/SKIPPED',
    completion_method VARCHAR(20) NOT NULL DEFAULT 'MANUAL' COMMENT '完成方式',
    dependency_node_instance_ids JSON COMMENT '前置依赖节点实例ID列表',
    is_required TINYINT(1) DEFAULT 1 COMMENT '是否必需节点',
    planned_date DATE COMMENT '计划完成日期',
    actual_date DATE COMMENT '实际完成日期',
    completed_by INT COMMENT '完成人ID',
    completed_at DATETIME COMMENT '完成时间',
    attachments JSON COMMENT '上传的附件列表',
    approval_record_id INT COMMENT '关联审批记录ID',
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_project_node_instances_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_project_node_instances_stage FOREIGN KEY (stage_instance_id) REFERENCES project_stage_instances(id) ON DELETE CASCADE,
    CONSTRAINT fk_project_node_instances_definition FOREIGN KEY (node_definition_id) REFERENCES node_definitions(id) ON DELETE SET NULL,
    CONSTRAINT fk_project_node_instances_completed_by FOREIGN KEY (completed_by) REFERENCES users(id),
    INDEX idx_project_node_instances_project (project_id),
    INDEX idx_project_node_instances_stage (stage_instance_id),
    INDEX idx_project_node_instances_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目节点实例表';

-- 6. 为 projects 表添加阶段模板关联字段
ALTER TABLE projects ADD COLUMN stage_template_id INT COMMENT '阶段模板ID';
ALTER TABLE projects ADD COLUMN current_stage_instance_id INT COMMENT '当前阶段实例ID';
ALTER TABLE projects ADD COLUMN current_node_instance_id INT COMMENT '当前节点实例ID';
ALTER TABLE projects ADD CONSTRAINT fk_projects_stage_template FOREIGN KEY (stage_template_id) REFERENCES stage_templates(id);
ALTER TABLE projects ADD INDEX idx_projects_stage_template (stage_template_id);
