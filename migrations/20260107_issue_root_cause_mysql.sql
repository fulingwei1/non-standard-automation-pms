-- ============================================
-- 问题原因和责任工程师字段扩展 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-07
-- 说明: 为问题表新增问题原因、责任工程师、库存损失和额外工时字段
-- ============================================

-- 问题原因和责任工程师字段扩展
ALTER TABLE issues 
ADD COLUMN root_cause VARCHAR(20) DEFAULT NULL COMMENT '问题原因：DESIGN_ERROR/MATERIAL_DEFECT/PROCESS_ERROR/EXTERNAL_FACTOR/OTHER',
ADD COLUMN responsible_engineer_id BIGINT DEFAULT NULL COMMENT '责任工程师ID',
ADD COLUMN responsible_engineer_name VARCHAR(50) DEFAULT NULL COMMENT '责任工程师姓名',
ADD COLUMN estimated_inventory_loss DECIMAL(14, 2) DEFAULT NULL COMMENT '预估库存损失金额',
ADD COLUMN estimated_extra_hours DECIMAL(10, 2) DEFAULT NULL COMMENT '预估额外工时(小时)';

-- 添加外键和索引
ALTER TABLE issues 
ADD CONSTRAINT fk_issues_responsible_engineer 
FOREIGN KEY (responsible_engineer_id) REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX idx_issues_responsible_engineer ON issues(responsible_engineer_id);
CREATE INDEX idx_issues_root_cause ON issues(root_cause);


