-- 合同付款节点与里程碑自动绑定功能
-- 创建日期: 2026-01-25
-- 描述: 添加payment_nodes字段到contracts表，添加milestone_id字段到payment_plans表

-- 1. 合同表添加付款节点相关字段（如果不存在）
-- SQLite doesn't support ADD COLUMN IF NOT EXISTS, so we need to use alter table with check

-- 先检查是否已有这些字段（通过尝试添加默认值）
-- SQLite会忽略已有列，但这样不够可靠，改用Python脚本处理

-- 2. 收款计划表添加里程碑关联字段
ALTER TABLE payment_plans ADD COLUMN milestone_id INTEGER;

-- 添加外键约束
ALTER TABLE payment_plans
ADD COLUMN milestone_id INTEGER;

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_payment_plans_milestone ON payment_plans(milestone_id);

-- 3. 添加注释
COMMENT ON COLUMN contracts.payment_nodes IS '付款节点列表，JSON格式：[{name, percentage, due_date, description}, ...]';
COMMENT ON COLUMN contracts.sow_text IS 'SOW（Statement of Work）文本描述';
COMMENT ON COLUMN contracts.acceptance_criteria IS '验收标准列表，JSON格式：[{criteria, type, description}, ...]';
COMMENT ON COLUMN payment_plans.milestone_id IS '关联的里程碑ID';
