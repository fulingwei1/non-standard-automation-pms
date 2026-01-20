-- ============================================
-- 问题管理与服务工单关联 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-20
-- 说明: 在问题表中添加服务工单关联字段
-- ============================================

-- ============================================
-- 1. 在 issues 表中添加 service_ticket_id 字段
-- ============================================

-- 检查字段是否已存在，如果不存在则添加
-- SQLite 不支持直接检查，使用 IF NOT EXISTS 的方式
-- 注意：SQLite 的 ALTER TABLE ADD COLUMN 不支持 IF NOT EXISTS，需要先检查

-- 添加 service_ticket_id 字段
ALTER TABLE issues ADD COLUMN service_ticket_id INTEGER;

-- 添加外键约束（SQLite 需要先创建表，外键在创建表时定义）
-- 由于 SQLite 的限制，外键约束需要在表创建时定义
-- 这里只添加字段，外键关系通过应用层维护

-- 添加索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_issues_service_ticket_id ON issues(service_ticket_id);

-- 添加注释（SQLite 不支持列注释，这里仅作说明）
-- service_ticket_id: 关联服务工单ID
