-- 售前系统集成迁移脚本 (MySQL)
-- 日期: 2026-01-10
-- 描述: 添加项目表的售前相关字段，支持线索转项目、中标预测、资源浪费分析

-- 1. 为 projects 表添加售前相关字段
ALTER TABLE projects
ADD COLUMN source_lead_id VARCHAR(50) COMMENT '来源线索号（如XS2501001）',
ADD COLUMN evaluation_score DECIMAL(5,2) COMMENT '评估总分',
ADD COLUMN predicted_win_rate DECIMAL(5,4) COMMENT '预测中标率（0-1）',
ADD COLUMN outcome VARCHAR(20) COMMENT '最终结果：PENDING/WON/LOST/ABANDONED',
ADD COLUMN loss_reason VARCHAR(50) COMMENT '丢标原因代码',
ADD COLUMN loss_reason_detail TEXT COMMENT '丢标原因详情',
ADD COLUMN salesperson_id INT COMMENT '销售人员ID',
ADD CONSTRAINT fk_projects_salesperson FOREIGN KEY (salesperson_id) REFERENCES users(id);

-- 2. 创建索引
CREATE INDEX idx_projects_source_lead ON projects(source_lead_id);
CREATE INDEX idx_projects_outcome ON projects(outcome);
CREATE INDEX idx_projects_salesperson ON projects(salesperson_id);

-- 3. 更新现有数据
-- 将已有合同的项目标记为中标
UPDATE projects SET outcome = 'WON' WHERE contract_id IS NOT NULL AND outcome IS NULL;
-- 将其他项目标记为进行中
UPDATE projects SET outcome = 'PENDING' WHERE outcome IS NULL;

-- 4. 项目阶段说明更新
-- S0: 售前跟进（评估通过，待签合同）- 新增
-- S1: 方案设计（原需求进入）
-- S2: 采购备料（原方案设计）
-- ... 后续阶段顺延
