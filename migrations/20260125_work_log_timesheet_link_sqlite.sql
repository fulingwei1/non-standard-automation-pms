-- ============================================================
-- 工作日志与工时记录关联 - SQLite 版本
-- 创建日期：2026-01-25
-- 说明：为work_logs表添加timesheet_id字段，建立与工时记录的关联
-- ============================================================

-- 添加timesheet_id字段
ALTER TABLE work_logs ADD COLUMN timesheet_id INTEGER;

-- 添加外键约束（SQLite不支持ALTER TABLE添加外键，需要在应用层保证一致性）
-- CREATE INDEX IF NOT EXISTS idx_work_log_timesheet ON work_logs(timesheet_id);

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_work_log_timesheet ON work_logs(timesheet_id);
