-- ============================================
-- 奖金分配明细表上传功能 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2025-01-15
-- 说明: 添加奖金分配明细表上传记录表
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 创建奖金分配明细表上传记录表
-- ============================================

CREATE TABLE IF NOT EXISTS `bonus_allocation_sheets` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `sheet_code` VARCHAR(50) NOT NULL COMMENT '明细表编号',
    `sheet_name` VARCHAR(200) NOT NULL COMMENT '明细表名称',
    
    -- 文件信息
    `file_path` VARCHAR(500) NOT NULL COMMENT '文件路径',
    `file_name` VARCHAR(200) COMMENT '原始文件名',
    `file_size` INT COMMENT '文件大小（字节）',
    
    -- 关联信息
    `project_id` INT UNSIGNED COMMENT '项目ID（可选）',
    `period_id` INT UNSIGNED COMMENT '考核周期ID（可选）',
    
    -- 统计信息
    `total_rows` INT DEFAULT 0 COMMENT '总行数',
    `valid_rows` INT DEFAULT 0 COMMENT '有效行数',
    `invalid_rows` INT DEFAULT 0 COMMENT '无效行数',
    
    -- 状态
    `status` VARCHAR(20) DEFAULT 'UPLOADED' COMMENT '状态：UPLOADED/PARSED/DISTRIBUTED',
    
    -- 解析结果
    `parse_result` JSON COMMENT '解析结果(JSON)',
    `parse_errors` JSON COMMENT '解析错误(JSON)',
    
    -- 线下确认标记
    `finance_confirmed` TINYINT(1) DEFAULT 0 COMMENT '财务部确认',
    `hr_confirmed` TINYINT(1) DEFAULT 0 COMMENT '人力资源部确认',
    `manager_confirmed` TINYINT(1) DEFAULT 0 COMMENT '总经理确认',
    `confirmed_at` DATETIME COMMENT '确认完成时间',
    
    -- 发放信息
    `distributed_at` DATETIME COMMENT '发放时间',
    `distributed_by` INT UNSIGNED COMMENT '发放人',
    `distribution_count` INT DEFAULT 0 COMMENT '发放记录数',
    
    `uploaded_by` INT UNSIGNED NOT NULL COMMENT '上传人',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_sheet_code` (`sheet_code`),
    KEY `idx_bonus_sheet_code` (`sheet_code`),
    KEY `idx_bonus_sheet_status` (`status`),
    KEY `idx_bonus_sheet_project` (`project_id`),
    KEY `idx_bonus_sheet_period` (`period_id`),
    CONSTRAINT `fk_bonus_sheet_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_bonus_sheet_period` FOREIGN KEY (`period_id`) REFERENCES `performance_period` (`id`),
    CONSTRAINT `fk_bonus_sheet_uploaded_by` FOREIGN KEY (`uploaded_by`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_bonus_sheet_distributed_by` FOREIGN KEY (`distributed_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='奖金分配明细表上传记录表';

SET FOREIGN_KEY_CHECKS = 1;


