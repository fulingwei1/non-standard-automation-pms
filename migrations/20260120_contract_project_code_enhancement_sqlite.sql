-- ============================================
-- 合同和项目编号管理增强 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2025-01-20
-- 说明: 增加客户合同编号字段和项目线索关联字段
-- ============================================

-- ============================================
-- 1. 合同表：增加客户合同编号字段
-- ============================================

-- SQLite 不支持 ALTER TABLE ADD COLUMN AFTER，需要重建表
-- 由于 SQLite 的限制，这里只添加字段，不指定位置

-- 检查字段是否存在，如果不存在则添加
-- SQLite 3.35.0+ 支持 ALTER TABLE ADD COLUMN IF NOT EXISTS
-- 为了兼容性，先检查表结构

-- 添加客户合同编号字段
ALTER TABLE `contracts` 
ADD COLUMN `customer_contract_no` VARCHAR(100) DEFAULT NULL;

-- 创建索引
CREATE INDEX IF NOT EXISTS `idx_contracts_customer_contract_no` ON `contracts` (`customer_contract_no`);

-- ============================================
-- 2. 项目表：增加客户合同编号和线索关联字段
-- ============================================

-- 添加客户合同编号字段
ALTER TABLE `projects` 
ADD COLUMN `customer_contract_no` VARCHAR(100) DEFAULT NULL;

-- 添加线索关联字段
ALTER TABLE `projects` 
ADD COLUMN `lead_id` INTEGER DEFAULT NULL;

-- 创建索引
CREATE INDEX IF NOT EXISTS `idx_projects_customer_contract_no` ON `projects` (`customer_contract_no`);
CREATE INDEX IF NOT EXISTS `idx_projects_lead` ON `projects` (`lead_id`);

-- 注意：SQLite 不支持外键约束的添加（需要重建表）
-- 外键约束需要在应用层或表创建时定义
-- 如果需要在 SQLite 中启用外键，需要执行：PRAGMA foreign_keys = ON;

-- ============================================
-- 迁移完成
-- ============================================
