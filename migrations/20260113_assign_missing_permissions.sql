-- ============================================
-- 权限分配脚本 - 将126个未分配的权限分配给相应角色
-- 生成日期: 2026-01-13
-- ============================================

-- 开始事务
BEGIN TRANSACTION;

-- ============================================
-- 1. ADMIN (id=21) - 获取所有未分配的权限
-- ============================================
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 21, p.id FROM permissions p
LEFT JOIN role_permissions rp ON p.id = rp.permission_id AND rp.role_id = 21
WHERE rp.id IS NULL AND p.is_active = 1;

-- ============================================
-- 2. GM (id=22) - 总经理：报表、数据导出、通知、预算审批
-- ============================================
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 22, id FROM permissions WHERE perm_code IN (
  'report:read', 'report:create', 'report:export', 'report:manage',
  'data_export:export', 'data_import_export:manage',
  'notification:read', 'notification:create',
  'budget:read', 'budget:approve',
  'cost:read', 'cost:manage',
  'project_evaluation:read', 'project_evaluation:manage'
) AND is_active = 1;

-- ============================================
-- 3. PROJECT_MANAGER (id=69) & PM (id=82) - 项目经理
-- ============================================
-- 项目相关权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 69, id FROM permissions WHERE perm_code IN (
  'stage:read', 'stage:create', 'stage:update', 'stage:delete', 'stage:manage',
  'milestone:read', 'milestone:create', 'milestone:update', 'milestone:delete',
  'task_center:read', 'task_center:create', 'task_center:update', 'task_center:assign', 'task_center:manage',
  'document:read', 'document:create', 'document:update', 'document:download',
  'project_role:read', 'project_role:create', 'project_role:update', 'project_role:assign',
  'project_evaluation:read', 'project_evaluation:create', 'project_evaluation:update',
  'machine:read', 'machine:create', 'machine:update',
  'issue:read', 'issue:create', 'issue:update', 'issue:assign', 'issue:resolve',
  'timesheet:read', 'timesheet:approve',
  'staff_matching:read', 'staff_matching:create', 'staff_matching:update'
) AND is_active = 1;

-- PM 角色同样权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 82, id FROM permissions WHERE perm_code IN (
  'stage:read', 'stage:create', 'stage:update', 'stage:manage',
  'milestone:read', 'milestone:create', 'milestone:update',
  'task_center:read', 'task_center:create', 'task_center:update', 'task_center:assign',
  'document:read', 'document:create', 'document:update', 'document:download',
  'project_role:read', 'project_role:assign',
  'project_evaluation:read', 'project_evaluation:create',
  'machine:read', 'machine:create', 'machine:update',
  'issue:read', 'issue:create', 'issue:update', 'issue:assign',
  'timesheet:read', 'timesheet:approve',
  'staff_matching:read'
) AND is_active = 1;

-- ============================================
-- 4. ENGINEER (id=5) - 工程师
-- ============================================
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 5, id FROM permissions WHERE perm_code IN (
  'technical_spec:read', 'technical_spec:create', 'technical_spec:update',
  'document:read', 'document:create', 'document:update', 'document:download',
  'machine:read', 'machine:update',
  'assembly_kit:read', 'assembly_kit:create', 'assembly_kit:update',
  'stage:read', 'stage:update',
  'milestone:read',
  'task_center:read', 'task_center:update',
  'issue:read', 'issue:create', 'issue:update', 'issue:resolve',
  'timesheet:read', 'timesheet:create', 'timesheet:update'
) AND is_active = 1;

-- ME/EE/SW 工程师
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.role_code IN ('ME', 'EE', 'SW') AND r.is_active = 1
AND p.perm_code IN (
  'technical_spec:read', 'technical_spec:create', 'technical_spec:update',
  'document:read', 'document:create', 'document:update', 'document:download',
  'machine:read', 'machine:update',
  'assembly_kit:read', 'assembly_kit:create', 'assembly_kit:update',
  'issue:read', 'issue:create', 'issue:update',
  'timesheet:read', 'timesheet:create', 'timesheet:update'
) AND p.is_active = 1;

-- ============================================
-- 5. PU/PU_MGR/PU_ENGINEER - 采购相关
-- ============================================
-- 采购经理
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 29, id FROM permissions WHERE perm_code IN (
  'supplier:read', 'supplier:create', 'supplier:update', 'supplier:delete',
  'material:read', 'material:create', 'material:update', 'material:delete',
  'cost:read', 'cost:create', 'cost:update', 'cost:manage',
  'shortage_alert:read', 'shortage_alert:create', 'shortage_alert:update', 'shortage_alert:resolve', 'shortage_alert:manage',
  'budget:read'
) AND is_active = 1;

-- 采购专员
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 34, id FROM permissions WHERE perm_code IN (
  'supplier:read', 'supplier:create', 'supplier:update',
  'material:read', 'material:create', 'material:update',
  'cost:read', 'cost:create', 'cost:update',
  'shortage_alert:read', 'shortage_alert:create', 'shortage_alert:update'
) AND is_active = 1;

-- 采购工程师
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 71, id FROM permissions WHERE perm_code IN (
  'supplier:read', 'supplier:create', 'supplier:update',
  'material:read', 'material:create', 'material:update',
  'cost:read', 'cost:create',
  'shortage_alert:read', 'shortage_alert:create', 'shortage_alert:update',
  'technical_spec:read'
) AND is_active = 1;

-- ============================================
-- 6. FINANCE/FI/CFO - 财务相关
-- ============================================
-- 财务总监
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 23, id FROM permissions WHERE perm_code IN (
  'budget:read', 'budget:create', 'budget:update', 'budget:approve', 'budget:delete',
  'cost:read', 'cost:create', 'cost:update', 'cost:delete', 'cost:manage',
  'hourly_rate:read', 'hourly_rate:create', 'hourly_rate:update', 'hourly_rate:delete',
  'report:read', 'report:export',
  'data_export:export'
) AND is_active = 1;

-- 财务人员/专员
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.role_code IN ('FINANCE', 'FI') AND r.is_active = 1
AND p.perm_code IN (
  'budget:read', 'budget:create', 'budget:update',
  'cost:read', 'cost:create', 'cost:update',
  'hourly_rate:read', 'hourly_rate:create', 'hourly_rate:update',
  'report:read'
) AND p.is_active = 1;

-- ============================================
-- 7. HR_MGR (id=68) - 人事经理
-- ============================================
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 68, id FROM permissions WHERE perm_code IN (
  'hr:read', 'hr:create', 'hr:update', 'hr:manage',
  'timesheet:read', 'timesheet:approve', 'timesheet:manage',
  'staff_matching:read', 'staff_matching:create', 'staff_matching:update', 'staff_matching:manage',
  'qualification:read', 'qualification:create', 'qualification:update', 'qualification:delete', 'qualification:manage',
  'report:read'
) AND is_active = 1;

-- ============================================
-- 8. SALES/SA/PRESALES/SALES_DIR - 销售相关
-- ============================================
-- 销售总监
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 25, id FROM permissions WHERE perm_code IN (
  'customer:read', 'customer:create', 'customer:update', 'customer:delete',
  'advantage_product:read', 'advantage_product:create', 'advantage_product:update', 'advantage_product:delete',
  'business_support:read', 'business_support:create', 'business_support:update', 'business_support:approve', 'business_support:manage',
  'presales_integration:read', 'presales_integration:create', 'presales_integration:update', 'presales_integration:manage',
  'report:read', 'report:export'
) AND is_active = 1;

-- 销售人员/专员
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.role_code IN ('SALES', 'SA') AND r.is_active = 1
AND p.perm_code IN (
  'customer:read', 'customer:create', 'customer:update',
  'advantage_product:read',
  'business_support:read', 'business_support:create', 'business_support:update',
  'presales_integration:read'
) AND p.is_active = 1;

-- 售前工程师
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 70, id FROM permissions WHERE perm_code IN (
  'customer:read',
  'advantage_product:read', 'advantage_product:create', 'advantage_product:update',
  'business_support:read', 'business_support:create',
  'presales_integration:read', 'presales_integration:create', 'presales_integration:update',
  'technical_spec:read', 'technical_spec:create',
  'document:read', 'document:create', 'document:download'
) AND is_active = 1;

-- ============================================
-- 9. QA/QA_MGR - 质量相关
-- ============================================
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.role_code IN ('QA', 'QA_MGR') AND r.is_active = 1
AND p.perm_code IN (
  'issue:read', 'issue:create', 'issue:update', 'issue:resolve',
  'document:read', 'document:download',
  'technical_spec:read',
  'report:read'
) AND p.is_active = 1;

-- QA_MGR 额外权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 28, id FROM permissions WHERE perm_code IN (
  'issue:assign', 'issue:delete',
  'qualification:read', 'qualification:create', 'qualification:update'
) AND is_active = 1;

-- ============================================
-- 10. PMC (id=27) - 计划管理
-- ============================================
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 27, id FROM permissions WHERE perm_code IN (
  'stage:read', 'stage:create', 'stage:update',
  'milestone:read', 'milestone:create', 'milestone:update',
  'shortage_alert:read', 'shortage_alert:create', 'shortage_alert:update', 'shortage_alert:resolve',
  'material:read',
  'supplier:read',
  'task_center:read', 'task_center:create', 'task_center:update',
  'report:read'
) AND is_active = 1;

-- ============================================
-- 11. PRODUCTION (id=72) - 生产
-- ============================================
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 72, id FROM permissions WHERE perm_code IN (
  'assembly_kit:read', 'assembly_kit:create', 'assembly_kit:update',
  'machine:read', 'machine:update',
  'stage:read', 'stage:update',
  'shortage_alert:read',
  'material:read',
  'issue:read', 'issue:create',
  'timesheet:read', 'timesheet:create', 'timesheet:update'
) AND is_active = 1;

-- ============================================
-- 12. ASSEMBLER (id=37) & DEBUG (id=38) - 装配/调试
-- ============================================
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.role_code IN ('ASSEMBLER', 'DEBUG') AND r.is_active = 1
AND p.perm_code IN (
  'assembly_kit:read',
  'machine:read',
  'document:read', 'document:download',
  'issue:read', 'issue:create',
  'timesheet:read', 'timesheet:create', 'timesheet:update'
) AND p.is_active = 1;

-- ============================================
-- 13. DEPT_MGR (id=81) - 部门经理
-- ============================================
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 81, id FROM permissions WHERE perm_code IN (
  'staff_matching:read', 'staff_matching:create', 'staff_matching:update',
  'timesheet:read', 'timesheet:approve',
  'task_center:read', 'task_center:assign',
  'report:read',
  'hr:read'
) AND is_active = 1;

-- ============================================
-- 14. 安装调度权限 - 给工程师和生产
-- ============================================
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.role_code IN ('ENGINEER', 'PRODUCTION', 'PROJECT_MANAGER', 'PM') AND r.is_active = 1
AND p.perm_code IN (
  'installation_dispatch:read', 'installation_dispatch:create', 'installation_dispatch:update'
) AND p.is_active = 1;

-- ADMIN 管理权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 21, id FROM permissions WHERE perm_code = 'installation_dispatch:manage' AND is_active = 1;

-- ============================================
-- 15. USER (id=73) - 普通用户：所有 read 权限
-- ============================================
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 73, id FROM permissions
WHERE perm_code LIKE '%:read' AND is_active = 1;

-- 通知权限给所有人
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 73, id FROM permissions
WHERE perm_code IN ('notification:read', 'notification:create', 'notification:update')
AND is_active = 1;

-- 提交事务
COMMIT;

-- 验证结果
SELECT '权限分配完成，统计结果:' as message;
SELECT
  '总权限数' as item,
  (SELECT COUNT(*) FROM permissions WHERE is_active = 1) as count
UNION ALL
SELECT
  '已分配权限数',
  (SELECT COUNT(DISTINCT permission_id) FROM role_permissions)
UNION ALL
SELECT
  '未分配权限数',
  (SELECT COUNT(*) FROM permissions p
   LEFT JOIN role_permissions rp ON p.id = rp.permission_id
   WHERE rp.id IS NULL AND p.is_active = 1);
