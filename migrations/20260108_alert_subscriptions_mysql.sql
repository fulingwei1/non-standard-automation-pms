-- ============================================
-- 预警订阅配置表 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-08
-- 说明: 用户预警订阅配置
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 预警订阅配置表
-- ============================================

CREATE TABLE IF NOT EXISTS `alert_subscriptions` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id`             INT UNSIGNED NOT NULL COMMENT '用户ID',
    `alert_type`          VARCHAR(50) DEFAULT NULL COMMENT '预警类型（空表示全部）',
    `project_id`          INT UNSIGNED DEFAULT NULL COMMENT '项目ID（空表示全部）',
    
    -- 订阅配置
    `min_level`           VARCHAR(20) DEFAULT 'WARNING' COMMENT '最低接收级别',
    `notify_channels`     JSON DEFAULT NULL COMMENT '通知渠道',
    
    -- 免打扰时段
    `quiet_start`         VARCHAR(10) DEFAULT NULL COMMENT '免打扰开始时间（HH:mm格式）',
    `quiet_end`           VARCHAR(10) DEFAULT NULL COMMENT '免打扰结束时间（HH:mm格式）',
    
    -- 状态
    `is_active`           TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    
    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    KEY `idx_alert_subscriptions_user` (`user_id`),
    KEY `idx_alert_subscriptions_type` (`alert_type`),
    KEY `idx_alert_subscriptions_project` (`project_id`),
    KEY `idx_alert_subscriptions_active` (`is_active`),
    CONSTRAINT `fk_alert_subscriptions_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_alert_subscriptions_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预警订阅配置表';

SET FOREIGN_KEY_CHECKS = 1;
