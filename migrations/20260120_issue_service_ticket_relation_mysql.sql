-- ============================================
-- 问题管理与服务工单关联 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-20
-- 说明: 在问题表中添加服务工单关联字段
-- ============================================

-- ============================================
-- 1. 在 issues 表中添加 service_ticket_id 字段
-- ============================================

-- 检查字段是否已存在，如果不存在则添加
SET @dbname = DATABASE();
SET @tablename = 'issues';
SET @columnname = 'service_ticket_id';
SET @preparedStatement = (SELECT IF(
    (
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
        WHERE
            (TABLE_SCHEMA = @dbname)
            AND (TABLE_NAME = @tablename)
            AND (COLUMN_NAME = @columnname)
    ) > 0,
    'SELECT 1',
    CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' INT NULL COMMENT ''关联服务工单ID''')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- 添加外键约束
-- 检查外键是否已存在
SET @fk_name = 'fk_issues_service_ticket';
SET @preparedStatement = (SELECT IF(
    (
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE
            (TABLE_SCHEMA = @dbname)
            AND (TABLE_NAME = @tablename)
            AND (CONSTRAINT_NAME = @fk_name)
    ) > 0,
    'SELECT 1',
    CONCAT('ALTER TABLE ', @tablename, ' ADD CONSTRAINT ', @fk_name, ' FOREIGN KEY (service_ticket_id) REFERENCES service_tickets(id) ON DELETE SET NULL')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- 添加索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_issues_service_ticket_id ON issues(service_ticket_id);
