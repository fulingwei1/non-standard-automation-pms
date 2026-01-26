-- 节点子任务功能 - MySQL 迁移脚本
-- 创建日期: 2026-01-20
-- 功能: 支持节点负责人分解子任务

-- 1. 为 project_node_instances 添加任务分解相关字段
ALTER TABLE project_node_instances
    ADD COLUMN assignee_id INT COMMENT '负责人ID',
    ADD COLUMN auto_complete_on_tasks TINYINT(1) DEFAULT 1 COMMENT '子任务全部完成时是否自动完成节点';

ALTER TABLE project_node_instances
    ADD CONSTRAINT fk_project_node_instances_assignee
    FOREIGN KEY (assignee_id) REFERENCES users(id);

CREATE INDEX idx_project_node_instances_assignee ON project_node_instances(assignee_id);

-- 2. 创建节点子任务表
CREATE TABLE IF NOT EXISTS node_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    node_instance_id INT NOT NULL COMMENT '所属节点实例ID',
    task_code VARCHAR(30) NOT NULL COMMENT '任务编码',
    task_name VARCHAR(200) NOT NULL COMMENT '任务名称',
    description TEXT COMMENT '任务描述',
    sequence INT NOT NULL DEFAULT 0 COMMENT '排序序号',

    -- 状态
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '状态: PENDING/IN_PROGRESS/COMPLETED/SKIPPED',

    -- 时间
    estimated_hours INT COMMENT '预计工时(小时)',
    actual_hours INT COMMENT '实际工时(小时)',
    planned_start_date DATE COMMENT '计划开始日期',
    planned_end_date DATE COMMENT '计划结束日期',
    actual_start_date DATE COMMENT '实际开始日期',
    actual_end_date DATE COMMENT '实际结束日期',

    -- 执行人
    assignee_id INT COMMENT '执行人ID',
    completed_by INT COMMENT '完成人ID',
    completed_at DATETIME COMMENT '完成时间',

    -- 优先级和标签
    priority VARCHAR(20) DEFAULT 'NORMAL' COMMENT '优先级: LOW/NORMAL/HIGH/URGENT',
    tags VARCHAR(200) COMMENT '标签(逗号分隔)',

    -- 附件和备注
    attachments JSON COMMENT '附件列表(JSON)',
    remark TEXT COMMENT '备注',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 外键约束
    CONSTRAINT fk_node_tasks_node_instance FOREIGN KEY (node_instance_id)
        REFERENCES project_node_instances(id) ON DELETE CASCADE,
    CONSTRAINT fk_node_tasks_assignee FOREIGN KEY (assignee_id)
        REFERENCES users(id),
    CONSTRAINT fk_node_tasks_completed_by FOREIGN KEY (completed_by)
        REFERENCES users(id),

    -- 索引
    INDEX idx_node_tasks_node_instance (node_instance_id),
    INDEX idx_node_tasks_status (status),
    INDEX idx_node_tasks_assignee (assignee_id),
    INDEX idx_node_tasks_priority (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='节点子任务表';
