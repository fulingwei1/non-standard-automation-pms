-- ============================================
-- 验收单客户签署文件上传功能 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2025-01-15
-- 说明: 添加客户签署验收单文件上传和正式完成标记字段
-- ============================================

-- ============================================
-- 更新验收单表，添加客户签署文件字段
-- ============================================

-- SQLite 不支持直接添加列到指定位置，只能添加到末尾
ALTER TABLE acceptance_orders
ADD COLUMN customer_signed_file_path VARCHAR(500) DEFAULT NULL; -- 客户签署的验收单文件路径

ALTER TABLE acceptance_orders
ADD COLUMN is_officially_completed BOOLEAN DEFAULT 0; -- 是否正式完成（已上传客户签署文件）

ALTER TABLE acceptance_orders
ADD COLUMN officially_completed_at DATETIME DEFAULT NULL; -- 正式完成时间

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_order_officially_completed ON acceptance_orders(is_officially_completed);


