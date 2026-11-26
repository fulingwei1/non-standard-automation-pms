-- 20261012_fix_foreign_key_violations_sqlite.sql
-- 修复历史遗留外键违规 (PRAGMA foreign_key_check -> 0)

-- 1. 补齐历史供应商数据 (修复 purchase_orders/goods_receipts/bom_items 等 179 处外键关联)
INSERT OR IGNORE INTO vendors (id, supplier_code, supplier_name, vendor_type, created_at, updated_at, tenant_id)
VALUES 
    (1, 'V001', '汇川技术（历史供应商）', 'MATERIAL', '2026-01-01 00:00:00', '2026-01-01 00:00:00', 1),
    (2, 'V002', '西门子（历史供应商）', 'MATERIAL', '2026-01-01 00:00:00', '2026-01-01 00:00:00', 1),
    (3, 'V003', '欧姆龙（历史供应商）', 'MATERIAL', '2026-01-01 00:00:00', '2026-01-01 00:00:00', 1);

-- 2. 补齐历史工人档案 (修复 work_order 48 处工单外键关联)
INSERT OR IGNORE INTO worker (id, worker_no, worker_name, status, is_active, created_at, updated_at, tenant_id)
VALUES 
    (36, 'WORKER000036', '装配工程师_36', 'ACTIVE', 1, '2026-01-01 00:00:00', '2026-01-01 00:00:00', 1),
    (37, 'WORKER000037', '装配工程师_37', 'ACTIVE', 1, '2026-01-01 00:00:00', '2026-01-01 00:00:00', 1),
    (38, 'WORKER000038', '装配工程师_38', 'ACTIVE', 1, '2026-01-01 00:00:00', '2026-01-01 00:00:00', 1),
    (39, 'WORKER000039', '装配工程师_39', 'ACTIVE', 1, '2026-01-01 00:00:00', '2026-01-01 00:00:00', 1);

-- 3. 修正售前费用关联的不存在项目 0 -> 默认项目 1 (4 处)
UPDATE presale_expenses SET project_id = 1 WHERE project_id = 0;

-- 4. 修正盘点明细任务关联偏移 (4->3, 7->6) (2 处)
UPDATE stock_count_detail SET task_id = 3 WHERE task_id = 4;
UPDATE stock_count_detail SET task_id = 6 WHERE task_id = 7;

-- 5. 修正 BOM 关联的历史已清理测试用户 -> 系统管理员 1 (2 处)
UPDATE bom_headers SET created_by = 1 WHERE created_by IN (196, 197);

-- 6. 修正权限审计关联的历史已清理测试用户 -> 系统管理员 1 (2 处)
UPDATE permission_audits SET operator_id = 1 WHERE operator_id = 199;
