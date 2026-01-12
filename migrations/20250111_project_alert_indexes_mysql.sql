-- 为 ProjectMember、AlertRecord、ExceptionEvent 表添加复合索引
-- 数据库: MySQL
-- 日期: 2025-01-11

-- ====================
-- project_members 表索引
-- ====================

-- user_id + is_active 复合索引（优化用户活跃成员查询）
CREATE INDEX IF NOT EXISTS idx_project_members_user_active 
ON project_members (user_id, is_active);

-- project_id + is_active 复合索引（优化项目活跃成员查询）
CREATE INDEX IF NOT EXISTS idx_project_members_project_active 
ON project_members (project_id, is_active);

-- machine_id + is_active 复合索引（优化设备活跃成员查询）
CREATE INDEX IF NOT EXISTS idx_project_members_machine_active 
ON project_members (machine_id, is_active);

-- 覆盖索引（减少回表查询）
CREATE INDEX IF NOT EXISTS idx_project_members_cover_user 
ON project_members (user_id, is_active, project_id);

-- ====================
-- alert_records 表索引
-- ====================

-- status + alert_level 复合索引（优化按状态和级别查询）
CREATE INDEX IF NOT EXISTS idx_alert_status_level 
ON alert_records (status, alert_level);

-- project_id + status 复合索引（优化项目预警状态查询）
CREATE INDEX IF NOT EXISTS idx_alert_project_status 
ON alert_records (project_id, status);

-- project_id + triggered_at 复合索引（优化项目预警时间查询）
CREATE INDEX IF NOT EXISTS idx_alert_project_time 
ON alert_records (project_id, triggered_at);

-- 覆盖索引（减少回表查询）
CREATE INDEX IF NOT EXISTS idx_alert_cover_status 
ON alert_records (status, triggered_at, alert_level, alert_title);

-- ====================
-- exception_events 表索引
-- ====================

-- status + is_overdue 复合索引（优化超期异常查询）
CREATE INDEX IF NOT EXISTS idx_event_status_overdue 
ON exception_events (status, is_overdue);

-- responsible_user_id + status 复合索引（优化责任人异常查询）
CREATE INDEX IF NOT EXISTS idx_event_responsible_status 
ON exception_events (responsible_user_id, status);

-- project_id + severity 复合索引（优化项目严重程度查询）
CREATE INDEX IF NOT EXISTS idx_event_project_severity 
ON exception_events (project_id, severity);

-- ====================
-- 验证索引创建
-- ====================

-- 查询 project_members 表的索引
SHOW INDEX FROM project_members 
WHERE Key_name IN (
    'idx_project_members_user_active',
    'idx_project_members_project_active',
    'idx_project_members_machine_active',
    'idx_project_members_cover_user'
);

-- 查询 alert_records 表的索引
SHOW INDEX FROM alert_records 
WHERE Key_name IN (
    'idx_alert_status_level',
    'idx_alert_project_status',
    'idx_alert_project_time',
    'idx_alert_cover_status'
);

-- 查询 exception_events 表的索引
SHOW INDEX FROM exception_events 
WHERE Key_name IN (
    'idx_event_status_overdue',
    'idx_event_responsible_status',
    'idx_event_project_severity'
);
