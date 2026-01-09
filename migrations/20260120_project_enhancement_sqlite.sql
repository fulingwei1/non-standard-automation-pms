-- ============================================
-- 项目模型增强 - SQLite 迁移文件
-- 创建日期: 2026-01-20
-- 说明: 扩展Project模型，覆盖泛微系统所有功能并超越
-- ============================================

-- 添加项目分类字段
ALTER TABLE projects ADD COLUMN project_category VARCHAR(20);

-- 添加销售关联字段
ALTER TABLE projects ADD COLUMN opportunity_id INTEGER;
ALTER TABLE projects ADD COLUMN contract_id INTEGER;

-- 添加ERP集成字段
ALTER TABLE projects ADD COLUMN erp_synced BOOLEAN DEFAULT 0;
ALTER TABLE projects ADD COLUMN erp_sync_time DATETIME;
ALTER TABLE projects ADD COLUMN erp_order_no VARCHAR(50);
ALTER TABLE projects ADD COLUMN erp_sync_status VARCHAR(20) DEFAULT 'PENDING';

-- 添加财务状态字段
ALTER TABLE projects ADD COLUMN invoice_issued BOOLEAN DEFAULT 0;
ALTER TABLE projects ADD COLUMN final_payment_completed BOOLEAN DEFAULT 0;
ALTER TABLE projects ADD COLUMN final_payment_date DATE;

-- 添加质保信息字段
ALTER TABLE projects ADD COLUMN warranty_period_months INTEGER;
ALTER TABLE projects ADD COLUMN warranty_start_date DATE;
ALTER TABLE projects ADD COLUMN warranty_end_date DATE;

-- 添加实施信息字段
ALTER TABLE projects ADD COLUMN implementation_address VARCHAR(500);
ALTER TABLE projects ADD COLUMN test_encryption VARCHAR(100);

-- 添加预立项流程关联字段
ALTER TABLE projects ADD COLUMN initiation_id INTEGER;

-- 添加外键约束
-- SQLite不支持ALTER TABLE ADD FOREIGN KEY，需要在应用层处理

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_projects_opportunity ON projects(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_projects_contract ON projects(contract_id);
CREATE INDEX IF NOT EXISTS idx_projects_erp_sync ON projects(erp_synced, erp_sync_status);
CREATE INDEX IF NOT EXISTS idx_projects_initiation ON projects(initiation_id);
CREATE INDEX IF NOT EXISTS idx_projects_category ON projects(project_category);
CREATE INDEX IF NOT EXISTS idx_projects_warranty_end ON projects(warranty_end_date);

-- 添加注释（SQLite不支持COMMENT，仅作说明）
-- project_category: 项目分类：销售/研发/改造/维保
-- opportunity_id: 销售机会ID
-- contract_id: 合同ID
-- erp_synced: 是否已录入ERP系统
-- erp_sync_time: ERP同步时间
-- erp_order_no: ERP订单号
-- erp_sync_status: ERP同步状态：PENDING/SYNCED/FAILED
-- invoice_issued: 是否已开票
-- final_payment_completed: 是否已结尾款
-- final_payment_date: 结尾款日期
-- warranty_period_months: 质保期限（月）
-- warranty_start_date: 质保开始日期
-- warranty_end_date: 质保结束日期
-- implementation_address: 实施地址
-- test_encryption: 测试加密
-- initiation_id: 预立项申请ID
