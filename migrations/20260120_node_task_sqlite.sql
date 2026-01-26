-- 节点子任务功能 - SQLite 迁移脚本
-- 创建日期: 2026-01-20
-- 功能: 支持节点负责人分解子任务

-- 1. 为 project_node_instances 添加任务分解相关字段
ALTER TABLE project_node_instances ADD COLUMN assignee_id INTEGER REFERENCES users(id);
ALTER TABLE project_node_instances ADD COLUMN auto_complete_on_tasks INTEGER DEFAULT 1;

-- 2. 创建节点子任务表
CREATE TABLE IF NOT EXISTS node_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_instance_id INTEGER NOT NULL REFERENCES project_node_instances(id) ON DELETE CASCADE,
    task_code VARCHAR(30) NOT NULL,
    task_name VARCHAR(200) NOT NULL,
    description TEXT,
    sequence INTEGER NOT NULL DEFAULT 0,

    -- 状态
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',

    -- 时间
    estimated_hours INTEGER,
    actual_hours INTEGER,
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,

    -- 执行人
    assignee_id INTEGER REFERENCES users(id),
    completed_by INTEGER REFERENCES users(id),
    completed_at DATETIME,

    -- 优先级和标签
    priority VARCHAR(20) DEFAULT 'NORMAL',
    tags VARCHAR(200),

    -- 附件和备注
    attachments TEXT,  -- JSON
    remark TEXT,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. 创建索引
CREATE INDEX IF NOT EXISTS idx_node_tasks_node_instance ON node_tasks(node_instance_id);
CREATE INDEX IF NOT EXISTS idx_node_tasks_status ON node_tasks(status);
CREATE INDEX IF NOT EXISTS idx_node_tasks_assignee ON node_tasks(assignee_id);
CREATE INDEX IF NOT EXISTS idx_node_tasks_priority ON node_tasks(priority);
CREATE INDEX IF NOT EXISTS idx_project_node_instances_assignee ON project_node_instances(assignee_id);
