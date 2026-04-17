-- 为 projects 补齐物料融合字段（兼容旧 SQLite 库）
-- 创建日期: 2026-04-16

ALTER TABLE projects ADD COLUMN kitting_rate NUMERIC(5, 1) DEFAULT 0;
ALTER TABLE projects ADD COLUMN material_status VARCHAR(20) DEFAULT '待采购';
ALTER TABLE projects ADD COLUMN shortage_items_count INTEGER DEFAULT 0;
