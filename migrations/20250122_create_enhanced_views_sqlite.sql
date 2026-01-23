-- ============================================================================
-- 数据库迁移脚本: 创建增强视图以改善数据访问
-- 版本: 20250122
-- 数据库: SQLite
-- ============================================================================

-- 说明: 此脚本创建视图以提供更丰富的数据访问方式，而不修改现有表结构
-- 这些视图可以作为冗余字段的替代方案，逐步迁移现有代码

-- ============================================================================
-- 1. 项目增强视图 - 包含关联的客户和项目经理信息
-- ============================================================================

CREATE VIEW IF NOT EXISTS project_enhanced_view AS
SELECT
    p.id,
    p.project_code,
    p.project_name,
    p.short_name,
    p.customer_id,
    -- 从关联表获取（替代冗余字段）
    c.customer_name,
    c.contact_person AS customer_contact,
    c.contact_phone AS customer_phone,
    c.contact_email AS customer_email,
    -- 项目经理信息
    p.pm_id,
    u.real_name AS pm_name,
    u.email AS pm_email,
    u.phone AS pm_phone,
    -- 部门信息
    p.dept_id,
    d.dept_name,
    -- 项目核心字段
    p.stage,
    p.status,
    p.health,
    p.progress_pct,
    p.contract_amount,
    p.budget_amount,
    p.actual_cost,
    p.planned_start_date,
    p.planned_end_date,
    p.actual_start_date,
    p.actual_end_date,
    p.is_active,
    p.is_archived,
    p.created_at,
    p.updated_at
FROM projects p
LEFT JOIN customers c ON p.customer_id = c.id
LEFT JOIN users u ON p.pm_id = u.id
LEFT JOIN departments d ON p.dept_id = d.id;

-- 创建视图索引（SQLite 不支持视图索引，但可以通过物化视图或触发器实现）

-- ============================================================================
-- 2. 设备增强视图 - 包含关联的项目和验收信息
-- ============================================================================

CREATE VIEW IF NOT EXISTS machine_enhanced_view AS
SELECT
    m.id,
    m.machine_code,
    m.machine_name,
    m.machine_no,
    m.project_id,
    p.project_name,
    p.customer_id,
    c.customer_name,
    -- 设备状态
    m.stage,
    m.status,
    m.health,
    m.progress_pct,
    -- 时间信息
    m.planned_start_date,
    m.planned_end_date,
    m.actual_start_date,
    m.actual_end_date,
    -- 验收信息
    m.fat_date,
    m.fat_result,
    m.sat_date,
    m.sat_result,
    -- 发货信息
    m.ship_date,
    m.ship_address,
    m.tracking_no,
    m.created_at,
    m.updated_at
FROM machines m
LEFT JOIN projects p ON m.project_id = p.id
LEFT JOIN customers c ON p.customer_id = c.id;

-- ============================================================================
-- 3. 项目成员增强视图 - 包含用户详细信息
-- ============================================================================

CREATE VIEW IF NOT EXISTS project_member_enhanced_view AS
SELECT
    pm.id,
    pm.project_id,
    p.project_code,
    p.project_name,
    pm.user_id,
    u.username,
    u.real_name AS user_name,
    u.employee_no,
    u.department,
    u.position,
    pm.role_code,
    pm.role_type_id,
    pm.is_lead,
    pm.allocation_pct,
    pm.start_date,
    pm.end_date,
    pm.commitment_level,
    pm.reporting_to_pm,
    pm.is_active,
    pm.created_at,
    pm.updated_at
FROM project_members pm
LEFT JOIN projects p ON pm.project_id = p.id
LEFT JOIN users u ON pm.user_id = u.id;

-- ============================================================================
-- 4. 项目成本汇总视图 - 聚合所有成本来源
-- ============================================================================

CREATE VIEW IF NOT EXISTS project_cost_summary_view AS
SELECT
    p.id AS project_id,
    p.project_code,
    p.project_name,
    -- 业务系统成本（采购、外协、BOM）
    COALESCE(SUM(pc.amount), 0) AS business_cost,
    -- 财务录入成本（差旅、人工等）
    COALESCE(SUM(fpc.amount), 0) AS financial_cost,
    -- 总成本
    COALESCE(SUM(pc.amount), 0) + COALESCE(SUM(fpc.amount), 0) AS total_cost,
    -- 预算
    p.budget_amount,
    -- 成本率
    CASE
        WHEN p.budget_amount > 0 THEN
            ROUND((COALESCE(SUM(pc.amount), 0) + COALESCE(SUM(fpc.amount), 0)) / p.budget_amount * 100, 2)
        ELSE 0
    END AS cost_ratio_pct
FROM projects p
LEFT JOIN project_costs pc ON p.id = pc.project_id
LEFT JOIN financial_project_costs fpc ON p.id = fpc.project_id
GROUP BY p.id, p.project_code, p.project_name, p.budget_amount;

-- ============================================================================
-- 5. 供应商统一视图 - 合并物料供应商和外协商
-- ============================================================================

-- 注意: 此视图依赖于 vendors 表的创建
-- 请先运行 20250122_merge_vendors_sqlite.sql 迁移脚本

CREATE VIEW IF NOT EXISTS vendor_unified_view AS
SELECT
    v.id,
    v.supplier_code AS vendor_code,
    v.supplier_name AS vendor_name,
    v.supplier_short_name AS vendor_short_name,
    v.vendor_type,
    v.contact_person,
    v.contact_phone,
    v.contact_email,
    v.address,
    v.bank_name,
    v.bank_account,
    v.tax_number,
    v.quality_rating,
    v.delivery_rating,
    v.service_rating,
    v.overall_rating,
    v.status,
    v.cooperation_start,
    v.last_order_date,
    v.created_at,
    v.updated_at
FROM vendors v;

-- ============================================================================
-- 使用示例
-- ============================================================================

-- 查询项目及其客户信息（无需多次 JOIN）
-- SELECT * FROM project_enhanced_view WHERE project_code = 'PJ2501001';

-- 查询设备及其项目信息
-- SELECT * FROM machine_enhanced_view WHERE machine_code = 'PN001';

-- 查询项目成本汇总
-- SELECT * FROM project_cost_summary_view WHERE cost_ratio_pct > 100;

-- ============================================================================
-- 回滚脚本（如果需要删除视图）
-- ============================================================================
-- DROP VIEW IF EXISTS project_enhanced_view;
-- DROP VIEW IF EXISTS machine_enhanced_view;
-- DROP VIEW IF EXISTS project_member_enhanced_view;
-- DROP VIEW IF EXISTS project_cost_summary_view;
-- DROP VIEW IF EXISTS vendor_unified_view;
