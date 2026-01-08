-- ============================================
-- 验收单客户签署文件上传功能 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2025-01-15
-- 说明: 添加客户签署验收单文件上传和正式完成标记字段
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 更新验收单表，添加客户签署文件字段
-- ============================================

ALTER TABLE `acceptance_orders`
ADD COLUMN `customer_signed_file_path` VARCHAR(500) DEFAULT NULL COMMENT '客户签署的验收单文件路径' AFTER `report_file_path`,
ADD COLUMN `is_officially_completed` TINYINT(1) DEFAULT 0 COMMENT '是否正式完成（已上传客户签署文件）' AFTER `customer_signed_file_path`,
ADD COLUMN `officially_completed_at` DATETIME DEFAULT NULL COMMENT '正式完成时间' AFTER `is_officially_completed`;

-- 添加索引
CREATE INDEX `idx_order_officially_completed` ON `acceptance_orders` (`is_officially_completed`);

SET FOREIGN_KEY_CHECKS = 1;


