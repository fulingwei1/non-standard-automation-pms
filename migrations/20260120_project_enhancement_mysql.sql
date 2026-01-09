-- ============================================
-- 项目模型增强 - MySQL 迁移文件
-- 创建日期: 2026-01-20
-- 说明: 扩展Project模型，覆盖泛微系统所有功能并超越
-- ============================================

-- 添加项目分类字段
ALTER TABLE projects 
ADD COLUMN project_category VARCHAR(20) COMMENT '项目分类：销售/研发/改造/维保';

-- 添加销售关联字段
ALTER TABLE projects 
ADD COLUMN opportunity_id INT COMMENT '销售机会ID',
ADD COLUMN contract_id INT COMMENT '合同ID';

-- 添加ERP集成字段
ALTER TABLE projects 
ADD COLUMN erp_synced BOOLEAN DEFAULT FALSE COMMENT '是否已录入ERP系统',
ADD COLUMN erp_sync_time DATETIME COMMENT 'ERP同步时间',
ADD COLUMN erp_order_no VARCHAR(50) COMMENT 'ERP订单号',
ADD COLUMN erp_sync_status VARCHAR(20) DEFAULT 'PENDING' COMMENT 'ERP同步状态：PENDING/SYNCED/FAILED';

-- 添加财务状态字段
ALTER TABLE projects 
ADD COLUMN invoice_issued BOOLEAN DEFAULT FALSE COMMENT '是否已开票',
ADD COLUMN final_payment_completed BOOLEAN DEFAULT FALSE COMMENT '是否已结尾款',
ADD COLUMN final_payment_date DATE COMMENT '结尾款日期';

-- 添加质保信息字段
ALTER TABLE projects 
ADD COLUMN warranty_period_months INT COMMENT '质保期限（月）',
ADD COLUMN warranty_start_date DATE COMMENT '质保开始日期',
ADD COLUMN warranty_end_date DATE COMMENT '质保结束日期';

-- 添加实施信息字段
ALTER TABLE projects 
ADD COLUMN implementation_address VARCHAR(500) COMMENT '实施地址',
ADD COLUMN test_encryption VARCHAR(100) COMMENT '测试加密';

-- 添加预立项流程关联字段
ALTER TABLE projects 
ADD COLUMN initiation_id INT COMMENT '预立项申请ID';

-- 添加外键约束
ALTER TABLE projects 
ADD CONSTRAINT fk_projects_opportunity FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE SET NULL,
ADD CONSTRAINT fk_projects_contract FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE SET NULL,
ADD CONSTRAINT fk_projects_initiation FOREIGN KEY (initiation_id) REFERENCES pmo_project_initiation(id) ON DELETE SET NULL;

-- 创建索引
CREATE INDEX idx_projects_opportunity ON projects(opportunity_id);
CREATE INDEX idx_projects_contract ON projects(contract_id);
CREATE INDEX idx_projects_erp_sync ON projects(erp_synced, erp_sync_status);
CREATE INDEX idx_projects_initiation ON projects(initiation_id);
CREATE INDEX idx_projects_category ON projects(project_category);
CREATE INDEX idx_projects_warranty_end ON projects(warranty_end_date);
