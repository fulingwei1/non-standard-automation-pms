-- 预警系统清理迁移脚本 - Phase 1 (SQLite)
-- 创建日期: 2026-01-21
-- 描述: 删除孤儿表（无模型引用、无数据）
-- 注意: 此脚本仅删除完全未使用的表，服务层依赖的表需要单独迁移

-- ============================================================
-- 前置检查：确认表为空
-- ============================================================
-- 运行以下查询确认表为空:
-- SELECT COUNT(*) FROM shortage_alerts;  -- 应为 0
-- SELECT COUNT(*) FROM mes_shortage_detail;  -- 应为 0

-- ============================================================
-- 删除孤儿表（无模型、无数据）
-- ============================================================

-- 1. shortage_alerts - 无对应 Model，0 行数据
DROP TABLE IF EXISTS shortage_alerts;

-- 2. mes_shortage_detail - 0 行数据，无外部引用
DROP TABLE IF EXISTS mes_shortage_detail;

-- ============================================================
-- 以下表暂不删除（有服务依赖，需要 Phase 2 迁移）
-- ============================================================
-- mat_shortage_alert: 0 行数据，但被 3 个服务引用:
--   - shortage_report_service.py
--   - progress_integration_service.py
--   - urgent_purchase_from_shortage_service.py
--
-- mes_shortage_alert_rule: 4 行数据，被 wechat_alert_service.py 引用
--
-- Phase 2 将迁移这些服务使用统一的 alert_records 表

-- ============================================================
-- 验证清理结果
-- ============================================================
-- 运行以下查询确认孤儿表已删除:
-- SELECT name FROM sqlite_master WHERE type='table' AND name IN ('shortage_alerts', 'mes_shortage_detail');
-- 结果应为空
