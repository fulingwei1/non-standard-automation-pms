-- ============================================
-- 合同和项目编号管理增强 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2025-01-20
-- 说明: 增加客户合同编号字段和项目线索关联字段
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. 合同表：增加客户合同编号字段
-- ============================================

ALTER TABLE `contracts` 
ADD COLUMN `customer_contract_no` VARCHAR(100) DEFAULT NULL COMMENT '客户合同编号（外部）' 
AFTER `contract_code`;

-- 添加索引便于查询
CREATE INDEX `idx_contracts_customer_contract_no` ON `contracts` (`customer_contract_no`);

-- ============================================
-- 2. 项目表：增加客户合同编号和线索关联字段
-- ============================================

ALTER TABLE `projects` 
ADD COLUMN `customer_contract_no` VARCHAR(100) DEFAULT NULL COMMENT '客户合同编号（外部编号）' 
AFTER `contract_no`;

ALTER TABLE `projects` 
ADD COLUMN `lead_id` INT UNSIGNED DEFAULT NULL COMMENT '关联线索ID' 
AFTER `opportunity_id`;

-- 添加外键约束
ALTER TABLE `projects` 
ADD CONSTRAINT `fk_projects_lead` 
FOREIGN KEY (`lead_id`) REFERENCES `leads` (`id`) 
ON DELETE SET NULL ON UPDATE CASCADE;

-- 添加索引便于查询
CREATE INDEX `idx_projects_customer_contract_no` ON `projects` (`customer_contract_no`);
CREATE INDEX `idx_projects_lead` ON `projects` (`lead_id`);

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================
-- 迁移完成
-- ============================================
