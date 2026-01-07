-- Migration: Add UI configuration fields to roles table
-- Date: 2026-01-06
-- Description: Add nav_groups and ui_config fields to support dynamic role configuration

-- SQLite version
ALTER TABLE roles ADD COLUMN nav_groups TEXT DEFAULT NULL;
ALTER TABLE roles ADD COLUMN ui_config TEXT DEFAULT NULL;

-- MySQL version (uncomment if using MySQL)
-- ALTER TABLE roles ADD COLUMN nav_groups JSON DEFAULT NULL COMMENT '导航组配置（JSON数组）';
-- ALTER TABLE roles ADD COLUMN ui_config JSON DEFAULT NULL COMMENT 'UI配置（JSON对象）';

-- Update existing roles with default configurations (optional)
-- This can be done via API or admin interface later


