-- 清理 Legacy 审批表迁移脚本
-- 创建日期: 2026-03-31
-- 描述: 删除已废弃的 4 个 legacy_ 前缀审批表
--       这些表来自旧的 WorkflowEngine，现已被统一审批引擎替代
-- 警告: 此操作不可逆，执行前请确认以下条件:
--   1. legacy_approval_instances 中无 PENDING/IN_PROGRESS 状态的记录
--   2. 所有历史数据已迁移到 approval_instances 表或已归档备份

-- ============================================================
-- 前置检查：确认无进行中的审批
-- ============================================================
-- 执行以下查询确认无活跃实例:
-- SELECT COUNT(*) FROM legacy_approval_instances
--   WHERE current_status IN ('PENDING', 'IN_PROGRESS');
-- 结果应为 0

-- ============================================================
-- 删除旧表（按外键依赖顺序）
-- ============================================================

-- 1. 删除审批记录（依赖 legacy_approval_instances 和 legacy_approval_nodes）
DROP TABLE IF EXISTS legacy_approval_records;

-- 2. 删除审批实例（依赖 legacy_approval_flows 和 legacy_approval_nodes）
DROP TABLE IF EXISTS legacy_approval_instances;

-- 3. 删除审批节点（依赖 legacy_approval_flows）
DROP TABLE IF EXISTS legacy_approval_nodes;

-- 4. 删除审批流程定义
DROP TABLE IF EXISTS legacy_approval_flows;

-- ============================================================
-- 验证清理结果
-- ============================================================
-- SELECT name FROM sqlite_master
--   WHERE type='table' AND name LIKE 'legacy_approval%'
--   ORDER BY name;
-- 应返回空结果
