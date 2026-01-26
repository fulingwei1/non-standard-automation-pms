-- 预警系统清理迁移脚本 - Phase 2 (SQLite)
-- 创建日期: 2026-01-21
-- 描述: 删除 mat_shortage_alert 表（服务已迁移到 alert_records）
-- 注意: ShortageAlertRule (mes_shortage_alert_rule) 保留用于 assembly_kit 模块

-- ============================================================
-- 前置检查：确认表为空
-- ============================================================
-- 运行以下查询确认表为空:
-- SELECT COUNT(*) FROM mat_shortage_alert;  -- 应为 0

-- ============================================================
-- 服务迁移情况（已完成）
-- ============================================================
-- 以下服务已从 ShortageAlert 迁移到 AlertRecord：
--
-- 1. progress_integration_service.py
--    - handle_shortage_alert_created() -> AlertRecord.target_type='SHORTAGE'
--    - handle_shortage_alert_resolved() -> AlertRecord 查询
--
-- 2. shortage_report_service.py
--    - calculate_alert_statistics() -> AlertRecord.target_type='SHORTAGE'
--    - calculate_response_time_statistics() -> AlertRecord 时间字段
--    - calculate_stoppage_statistics() -> AlertRecord.alert_data JSON
--
-- 3. urgent_purchase_from_shortage_service.py
--    - create_urgent_purchase_request_from_alert() -> AlertRecord
--    - auto_trigger_urgent_purchase_for_alerts() -> AlertRecord 查询
--
-- 4. alerts_crud.py
--    - update_shortage_alert() -> AlertRecord 进度联动
--    - resolve_shortage_alert() -> AlertRecord 进度联动

-- ============================================================
-- 删除空的 mat_shortage_alert 表
-- ============================================================
-- 此表已被 alert_records 表替代，通过 target_type='SHORTAGE' 筛选

DROP TABLE IF EXISTS mat_shortage_alert;

-- ============================================================
-- 保留的表（有业务价值）
-- ============================================================
-- mes_shortage_alert_rule: 4 行数据，用于 assembly_kit 模块的预警规则配置
-- 此表是 assembly_kit 模块的专用配置表，与通用的 alert_rules 表分离
-- 保留以支持装配齐套分析的专用预警规则

-- ============================================================
-- 验证清理结果
-- ============================================================
-- 运行以下查询确认表已删除:
-- SELECT name FROM sqlite_master WHERE type='table' AND name='mat_shortage_alert';
-- 结果应为空

-- 确认 alert_records 有缺料预警数据:
-- SELECT COUNT(*) FROM alert_records WHERE target_type='SHORTAGE';

-- ============================================================
-- 后续清理（需手动在代码中执行）
-- ============================================================
-- 1. 删除 app/models/shortage/alerts.py 中的 ShortageAlert 类
-- 2. 更新 app/models/shortage/__init__.py 中的导出
-- 3. 更新 app/models/__init__.py 中的导出
