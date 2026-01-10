-- ============================================================
-- 工作日志与工时记录关联 - MySQL 版本
-- 创建日期：2026-01-25
-- 说明：为work_logs表添加timesheet_id字段，建立与工时记录的关联
-- ============================================================

-- 添加timesheet_id字段
ALTER TABLE work_logs 
ADD COLUMN timesheet_id INT COMMENT '关联的工时记录ID',
ADD INDEX idx_work_log_timesheet (timesheet_id),
ADD CONSTRAINT fk_work_log_timesheet 
    FOREIGN KEY (timesheet_id) REFERENCES timesheet(id) 
    ON DELETE SET NULL;
