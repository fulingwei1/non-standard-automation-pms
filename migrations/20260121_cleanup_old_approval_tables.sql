-- 清理旧审批表迁移脚本 (SQLite)
-- 创建日期: 2026-01-21
-- 描述: 删除已废弃的 13 个旧审批表（数据已迁移到统一审批系统）
-- 警告: 此操作不可逆，请确保数据已迁移完成

-- ============================================================
-- 前置检查：确认数据已迁移
-- ============================================================
-- 运行以下查询确认迁移完成:
-- SELECT COUNT(*) FROM approval_instances WHERE entity_type = 'TASK';  -- 应为 59
-- SELECT COUNT(*) FROM task_approval_workflows;  -- 应为 59

-- ============================================================
-- 删除旧表（按依赖顺序）
-- ============================================================

-- 1. 删除通用审批表
DROP TABLE IF EXISTS approval_history;
DROP TABLE IF EXISTS approval_records;
DROP TABLE IF EXISTS approval_workflow_steps;
DROP TABLE IF EXISTS approval_workflows;

-- 2. 删除业务特定审批表
DROP TABLE IF EXISTS contract_approvals;
DROP TABLE IF EXISTS ecn_approval_matrix;
DROP TABLE IF EXISTS ecn_approvals;
DROP TABLE IF EXISTS invoice_approvals;
DROP TABLE IF EXISTS quote_approvals;
DROP TABLE IF EXISTS quote_cost_approvals;
DROP TABLE IF EXISTS role_assignment_approvals;
DROP TABLE IF EXISTS timesheet_approval_log;

-- 3. 删除已迁移的任务审批表
DROP TABLE IF EXISTS task_approval_workflows;

-- ============================================================
-- 验证清理结果
-- ============================================================
-- 运行以下查询确认旧表已删除:
-- SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%approval%' ORDER BY name;
-- 应只剩下以 approval_ 开头的 13 个新表
