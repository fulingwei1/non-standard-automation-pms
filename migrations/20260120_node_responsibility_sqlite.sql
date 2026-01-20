-- 节点责任分配与交付物扩展 - SQLite 迁移脚本
-- 创建日期: 2026-01-20

-- 1. NodeDefinition 新增字段
ALTER TABLE node_definitions ADD COLUMN owner_role_code VARCHAR(50);
ALTER TABLE node_definitions ADD COLUMN participant_role_codes TEXT;
ALTER TABLE node_definitions ADD COLUMN deliverables TEXT;

-- 2. ProjectNodeInstance 新增字段
ALTER TABLE project_node_instances ADD COLUMN owner_role_code VARCHAR(50);
ALTER TABLE project_node_instances ADD COLUMN participant_role_codes TEXT;
ALTER TABLE project_node_instances ADD COLUMN deliverables TEXT;
ALTER TABLE project_node_instances ADD COLUMN owner_id INTEGER REFERENCES users(id);
ALTER TABLE project_node_instances ADD COLUMN participant_ids TEXT;

-- 3. 创建索引
CREATE INDEX IF NOT EXISTS idx_node_definitions_owner_role ON node_definitions(owner_role_code);
CREATE INDEX IF NOT EXISTS idx_project_node_instances_owner ON project_node_instances(owner_id);
CREATE INDEX IF NOT EXISTS idx_project_node_instances_owner_role ON project_node_instances(owner_role_code);
