-- ============================================
-- 研发项目工作日志和文档管理扩展 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-08
-- 说明: 为Timesheet和ProjectDocument添加rd_project_id字段，支持研发项目
-- ============================================

-- ============================================
-- 1. 为工时记录表添加研发项目关联
-- ============================================

ALTER TABLE `timesheet` 
ADD COLUMN `rd_project_id` INT UNSIGNED DEFAULT NULL COMMENT '研发项目ID（可选，如果填写则直接关联研发项目）' AFTER `project_id`;

-- 添加外键约束
ALTER TABLE `timesheet`
ADD CONSTRAINT `fk_timesheet_rd_project` 
FOREIGN KEY (`rd_project_id`) REFERENCES `rd_project` (`id`) ON DELETE SET NULL;

-- 添加索引
CREATE INDEX `idx_ts_rd_project` ON `timesheet` (`rd_project_id`);

-- ============================================
-- 2. 为项目文档表添加研发项目关联
-- ============================================

ALTER TABLE `project_documents` 
ADD COLUMN `rd_project_id` INT UNSIGNED DEFAULT NULL COMMENT '研发项目ID（可选，如果填写则直接关联研发项目）' AFTER `project_id`;

-- 添加外键约束
ALTER TABLE `project_documents`
ADD CONSTRAINT `fk_project_documents_rd_project` 
FOREIGN KEY (`rd_project_id`) REFERENCES `rd_project` (`id`) ON DELETE SET NULL;

-- 添加索引
CREATE INDEX `idx_project_documents_rd_project` ON `project_documents` (`rd_project_id`);





