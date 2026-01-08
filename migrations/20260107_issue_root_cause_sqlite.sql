-- ============================================
-- 问题原因和责任工程师字段扩展 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-07
-- 说明: 为问题表新增问题原因、责任工程师、库存损失和额外工时字段
-- ============================================

PRAGMA foreign_keys = ON;

-- 问题原因和责任工程师字段扩展
ALTER TABLE issues 
ADD COLUMN root_cause VARCHAR(20) DEFAULT NULL; -- 问题原因：DESIGN_ERROR/MATERIAL_DEFECT/PROCESS_ERROR/EXTERNAL_FACTOR/OTHER

ALTER TABLE issues 
ADD COLUMN responsible_engineer_id INTEGER DEFAULT NULL; -- 责任工程师ID

ALTER TABLE issues 
ADD COLUMN responsible_engineer_name VARCHAR(50) DEFAULT NULL; -- 责任工程师姓名

ALTER TABLE issues 
ADD COLUMN estimated_inventory_loss DECIMAL(14, 2) DEFAULT NULL; -- 预估库存损失金额

ALTER TABLE issues 
ADD COLUMN estimated_extra_hours DECIMAL(10, 2) DEFAULT NULL; -- 预估额外工时(小时)

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_issues_responsible_engineer ON issues(responsible_engineer_id);
CREATE INDEX IF NOT EXISTS idx_issues_root_cause ON issues(root_cause);
