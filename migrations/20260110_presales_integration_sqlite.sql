-- 售前系统集成迁移脚本 (SQLite)
-- 日期: 2026-01-10
-- 描述: 添加项目表的售前相关字段，支持线索转项目、中标预测、资源浪费分析

-- 1. 为 projects 表添加售前相关字段
ALTER TABLE projects ADD COLUMN source_lead_id VARCHAR(50);  -- 来源线索号（如XS2501001）
ALTER TABLE projects ADD COLUMN evaluation_score DECIMAL(5,2);  -- 评估总分
ALTER TABLE projects ADD COLUMN predicted_win_rate DECIMAL(5,4);  -- 预测中标率（0-1）
ALTER TABLE projects ADD COLUMN outcome VARCHAR(20);  -- 最终结果：PENDING/WON/LOST/ABANDONED
ALTER TABLE projects ADD COLUMN loss_reason VARCHAR(50);  -- 丢标原因代码
ALTER TABLE projects ADD COLUMN loss_reason_detail TEXT;  -- 丢标原因详情
ALTER TABLE projects ADD COLUMN salesperson_id INTEGER REFERENCES users(id);  -- 销售人员ID

-- 2. 创建索引
CREATE INDEX IF NOT EXISTS idx_projects_source_lead ON projects(source_lead_id);
CREATE INDEX IF NOT EXISTS idx_projects_outcome ON projects(outcome);
CREATE INDEX IF NOT EXISTS idx_projects_salesperson ON projects(salesperson_id);

-- 3. 更新项目阶段说明
-- S0: 售前跟进（评估通过，待签合同）- 新增
-- S1: 方案设计（原需求进入）
-- S2: 采购备料（原方案设计）
-- ... 后续阶段顺延

-- 注意：SQLite 不支持直接修改表结构，如需添加约束，需重建表
-- 现有数据的 outcome 可设置为 NULL 或 'PENDING'
UPDATE projects SET outcome = 'WON' WHERE contract_id IS NOT NULL AND outcome IS NULL;
UPDATE projects SET outcome = 'PENDING' WHERE outcome IS NULL;
