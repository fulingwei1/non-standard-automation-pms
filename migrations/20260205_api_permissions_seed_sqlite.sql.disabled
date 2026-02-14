-- ============================================
-- API 权限种子数据 - SQLite
-- 版本: 1.0
-- 日期: 2026-02-05
-- 说明: 为 api_permissions 表填充所有端点实际使用的权限码，
--       并为现有角色分配对应权限（通过 role_api_permissions 表）
-- ============================================

-- ============================================
-- 1. API 权限定义
-- ============================================

-- 先清理可能的脏数据（幂等）
-- DELETE FROM role_api_permissions;
-- DELETE FROM api_permissions;

-- 用户管理权限（统一为小写冒号格式）
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'user:view', '查看用户', 'USER', 'VIEW', 'API', 1, 1),
(NULL, 'user:create', '创建用户', 'USER', 'CREATE', 'API', 1, 1),
(NULL, 'user:update', '编辑用户', 'USER', 'UPDATE', 'API', 1, 1),
(NULL, 'user:delete', '删除用户', 'USER', 'DELETE', 'API', 1, 1);

-- 角色管理权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'role:view', '查看角色', 'ROLE', 'VIEW', 'API', 1, 1),
(NULL, 'role:create', '创建角色', 'ROLE', 'CREATE', 'API', 1, 1),
(NULL, 'role:update', '编辑角色', 'ROLE', 'UPDATE', 'API', 1, 1),
(NULL, 'role:delete', '删除角色', 'ROLE', 'DELETE', 'API', 1, 1),
(NULL, 'role:assign', '分配角色', 'ROLE', 'EDIT', 'API', 1, 1);

-- 审计权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'audit:view', '查看审计日志', 'AUDIT', 'VIEW', 'API', 1, 1);

-- 项目管理权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'project:read', '查看项目', 'PROJECT', 'VIEW', 'API', 1, 1),
(NULL, 'project:create', '创建项目', 'PROJECT', 'CREATE', 'API', 1, 1),
(NULL, 'project:update', '编辑项目', 'PROJECT', 'EDIT', 'API', 1, 1),
(NULL, 'project:delete', '删除项目', 'PROJECT', 'DELETE', 'API', 1, 1),
(NULL, 'project:erp:sync', 'ERP同步项目', 'PROJECT', 'EDIT', 'API', 1, 1),
(NULL, 'project:erp:update', 'ERP更新项目', 'PROJECT', 'EDIT', 'API', 1, 1);

-- 机台管理权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'machine:read', '查看机台', 'MACHINE', 'VIEW', 'API', 1, 1),
(NULL, 'machine:create', '创建机台', 'MACHINE', 'CREATE', 'API', 1, 1),
(NULL, 'machine:update', '编辑机台', 'MACHINE', 'EDIT', 'API', 1, 1),
(NULL, 'machine:delete', '删除机台', 'MACHINE', 'DELETE', 'API', 1, 1);

-- 里程碑管理权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'milestone:read', '查看里程碑', 'MILESTONE', 'VIEW', 'API', 1, 1),
(NULL, 'milestone:create', '创建里程碑', 'MILESTONE', 'CREATE', 'API', 1, 1),
(NULL, 'milestone:update', '编辑里程碑', 'MILESTONE', 'EDIT', 'API', 1, 1),
(NULL, 'milestone:delete', '删除里程碑', 'MILESTONE', 'DELETE', 'API', 1, 1);

-- 问题管理权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'issue:read', '查看问题', 'ISSUE', 'VIEW', 'API', 1, 1),
(NULL, 'issue:create', '创建问题', 'ISSUE', 'CREATE', 'API', 1, 1),
(NULL, 'issue:update', '编辑问题', 'ISSUE', 'EDIT', 'API', 1, 1),
(NULL, 'issue:delete', '删除问题', 'ISSUE', 'DELETE', 'API', 1, 1);

-- 工时管理权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'timesheet:read', '查看工时', 'TIMESHEET', 'VIEW', 'API', 1, 1),
(NULL, 'timesheet:create', '填报工时', 'TIMESHEET', 'CREATE', 'API', 1, 1),
(NULL, 'timesheet:update', '编辑工时', 'TIMESHEET', 'EDIT', 'API', 1, 1),
(NULL, 'timesheet:delete', '删除工时', 'TIMESHEET', 'DELETE', 'API', 1, 1),
(NULL, 'timesheet:submit', '提交工时', 'TIMESHEET', 'APPROVE', 'API', 1, 1);

-- 文档管理权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'document:read', '查看文档', 'DOCUMENT', 'VIEW', 'API', 1, 1),
(NULL, 'document:create', '创建文档', 'DOCUMENT', 'CREATE', 'API', 1, 1),
(NULL, 'document:update', '编辑文档', 'DOCUMENT', 'EDIT', 'API', 1, 1),
(NULL, 'document:delete', '删除文档', 'DOCUMENT', 'DELETE', 'API', 1, 1);

-- 客户管理权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'customer:read', '查看客户', 'CUSTOMER', 'VIEW', 'API', 1, 1),
(NULL, 'customer:create', '创建客户', 'CUSTOMER', 'CREATE', 'API', 1, 1),
(NULL, 'customer:update', '编辑客户', 'CUSTOMER', 'EDIT', 'API', 1, 1),
(NULL, 'customer:delete', '删除客户', 'CUSTOMER', 'DELETE', 'API', 1, 1);

-- 供应商管理权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'supplier:read', '查看供应商', 'SUPPLIER', 'VIEW', 'API', 1, 1),
(NULL, 'supplier:create', '创建供应商', 'SUPPLIER', 'CREATE', 'API', 1, 1),
(NULL, 'supplier:update', '编辑供应商', 'SUPPLIER', 'EDIT', 'API', 1, 1),
(NULL, 'supplier:delete', '删除供应商', 'SUPPLIER', 'DELETE', 'API', 1, 1);

-- 装配套件权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'assembly_kit:read', '查看装配套件', 'ASSEMBLY_KIT', 'VIEW', 'API', 1, 1),
(NULL, 'assembly_kit:create', '创建装配套件', 'ASSEMBLY_KIT', 'CREATE', 'API', 1, 1),
(NULL, 'assembly_kit:update', '编辑装配套件', 'ASSEMBLY_KIT', 'EDIT', 'API', 1, 1),
(NULL, 'assembly_kit:delete', '删除装配套件', 'ASSEMBLY_KIT', 'DELETE', 'API', 1, 1);

-- 预算管理权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'budget:read', '查看预算', 'BUDGET', 'VIEW', 'API', 1, 1),
(NULL, 'budget:create', '创建预算', 'BUDGET', 'CREATE', 'API', 1, 1),
(NULL, 'budget:approve', '审批预算', 'BUDGET', 'APPROVE', 'API', 1, 1);

-- 商务支持权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'business_support:read', '查看商务支持', 'BUSINESS_SUPPORT', 'VIEW', 'API', 1, 1),
(NULL, 'business_support:create', '创建商务支持', 'BUSINESS_SUPPORT', 'CREATE', 'API', 1, 1),
(NULL, 'business_support:update', '编辑商务支持', 'BUSINESS_SUPPORT', 'EDIT', 'API', 1, 1),
(NULL, 'business_support:approve', '审批商务支持', 'BUSINESS_SUPPORT', 'APPROVE', 'API', 1, 1);

-- 成本管理权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'cost:read', '查看成本', 'COST', 'VIEW', 'API', 1, 1);

-- 工程师绩效权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'engineer:read', '查看工程师绩效', 'ENGINEER', 'VIEW', 'API', 1, 1),
(NULL, 'engineer:create', '录入工程师绩效', 'ENGINEER', 'CREATE', 'API', 1, 1);

-- 财务管理权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'finance:read', '查看财务数据', 'FINANCE', 'VIEW', 'API', 1, 1);

-- HR 权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'hr:read', '查看HR数据', 'HR', 'VIEW', 'API', 1, 1),
(NULL, 'hr:create', '录入HR数据', 'HR', 'CREATE', 'API', 1, 1);

-- 工时费率权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'hourly_rate:read', '查看工时费率', 'HOURLY_RATE', 'VIEW', 'API', 1, 1),
(NULL, 'hourly_rate:create', '创建工时费率', 'HOURLY_RATE', 'CREATE', 'API', 1, 1),
(NULL, 'hourly_rate:update', '编辑工时费率', 'HOURLY_RATE', 'EDIT', 'API', 1, 1),
(NULL, 'hourly_rate:delete', '删除工时费率', 'HOURLY_RATE', 'DELETE', 'API', 1, 1);

-- 安装派遣权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'installation_dispatch:read', '查看安装派遣', 'INSTALLATION', 'VIEW', 'API', 1, 1),
(NULL, 'installation_dispatch:create', '创建安装派遣', 'INSTALLATION', 'CREATE', 'API', 1, 1),
(NULL, 'installation_dispatch:update', '编辑安装派遣', 'INSTALLATION', 'EDIT', 'API', 1, 1);

-- 通知管理权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'notification:read', '查看通知', 'NOTIFICATION', 'VIEW', 'API', 1, 1),
(NULL, 'notification:delete', '删除通知', 'NOTIFICATION', 'DELETE', 'API', 1, 1);

-- 绩效管理权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'performance:manage', '管理绩效', 'PERFORMANCE', 'EDIT', 'API', 1, 1);

-- 售前分析权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'presale_analytics:create', '创建售前分析', 'PRESALE', 'CREATE', 'API', 1, 1);

-- 采购管理权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'procurement:read', '查看采购', 'PROCUREMENT', 'VIEW', 'API', 1, 1);

-- 项目评价权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'project_evaluation:read', '查看项目评价', 'PROJECT_EVAL', 'VIEW', 'API', 1, 1),
(NULL, 'project_evaluation:create', '创建项目评价', 'PROJECT_EVAL', 'CREATE', 'API', 1, 1),
(NULL, 'project_evaluation:update', '编辑项目评价', 'PROJECT_EVAL', 'EDIT', 'API', 1, 1);

-- 项目角色权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'project_role:read', '查看项目角色', 'PROJECT_ROLE', 'VIEW', 'API', 1, 1),
(NULL, 'project_role:create', '创建项目角色', 'PROJECT_ROLE', 'CREATE', 'API', 1, 1),
(NULL, 'project_role:update', '编辑项目角色', 'PROJECT_ROLE', 'EDIT', 'API', 1, 1),
(NULL, 'project_role:delete', '删除项目角色', 'PROJECT_ROLE', 'DELETE', 'API', 1, 1),
(NULL, 'project_role:assign', '分配项目角色', 'PROJECT_ROLE', 'EDIT', 'API', 1, 1);

-- 研发项目权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'rd_project:read', '查看研发项目', 'RD_PROJECT', 'VIEW', 'API', 1, 1);

-- 报表管理权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'report:read', '查看报表', 'REPORT', 'VIEW', 'API', 1, 1),
(NULL, 'report:create', '创建报表', 'REPORT', 'CREATE', 'API', 1, 1),
(NULL, 'report:export', '导出报表', 'REPORT', 'EXPORT', 'API', 1, 1);

-- 人员匹配权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'staff_matching:read', '查看人员匹配', 'STAFF_MATCHING', 'VIEW', 'API', 1, 1),
(NULL, 'staff_matching:create', '创建人员匹配', 'STAFF_MATCHING', 'CREATE', 'API', 1, 1),
(NULL, 'staff_matching:update', '编辑人员匹配', 'STAFF_MATCHING', 'EDIT', 'API', 1, 1);

-- 任务中心权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'task_center:read', '查看任务', 'TASK_CENTER', 'VIEW', 'API', 1, 1),
(NULL, 'task_center:create', '创建任务', 'TASK_CENTER', 'CREATE', 'API', 1, 1),
(NULL, 'task_center:update', '编辑任务', 'TASK_CENTER', 'EDIT', 'API', 1, 1),
(NULL, 'task_center:assign', '分配任务', 'TASK_CENTER', 'EDIT', 'API', 1, 1);

-- 技术规格权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'technical_spec:read', '查看技术规格', 'TECHNICAL_SPEC', 'VIEW', 'API', 1, 1),
(NULL, 'technical_spec:create', '创建技术规格', 'TECHNICAL_SPEC', 'CREATE', 'API', 1, 1),
(NULL, 'technical_spec:update', '编辑技术规格', 'TECHNICAL_SPEC', 'EDIT', 'API', 1, 1),
(NULL, 'technical_spec:delete', '删除技术规格', 'TECHNICAL_SPEC', 'DELETE', 'API', 1, 1);

-- 工作日志配置权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'work_log:config:read', '查看工作日志配置', 'WORK_LOG', 'VIEW', 'API', 1, 1),
(NULL, 'work_log:config:create', '创建工作日志配置', 'WORK_LOG', 'CREATE', 'API', 1, 1),
(NULL, 'work_log:config:update', '编辑工作日志配置', 'WORK_LOG', 'EDIT', 'API', 1, 1);

-- 优势产品权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'advantage_product:read', '查看优势产品', 'ADVANTAGE_PRODUCT', 'VIEW', 'API', 1, 1),
(NULL, 'advantage_product:create', '创建优势产品', 'ADVANTAGE_PRODUCT', 'CREATE', 'API', 1, 1),
(NULL, 'advantage_product:update', '编辑优势产品', 'ADVANTAGE_PRODUCT', 'EDIT', 'API', 1, 1),
(NULL, 'advantage_product:delete', '删除优势产品', 'ADVANTAGE_PRODUCT', 'DELETE', 'API', 1, 1);

-- 数据导入导出权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'data_import_export:manage', '管理数据导入导出', 'DATA_MGMT', 'EDIT', 'API', 1, 1);

-- ECN (工程变更通知) 权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'ecn:read', '查看ECN', 'ECN', 'VIEW', 'API', 1, 1),
(NULL, 'ecn:create', '创建ECN', 'ECN', 'CREATE', 'API', 1, 1),
(NULL, 'ecn:update', '编辑ECN', 'ECN', 'EDIT', 'API', 1, 1),
(NULL, 'ecn:submit', '提交ECN', 'ECN', 'EDIT', 'API', 1, 1),
(NULL, 'ecn:approve', '审批ECN', 'ECN', 'APPROVE', 'API', 1, 1),
(NULL, 'ecn:cancel', '取消ECN', 'ECN', 'EDIT', 'API', 1, 1);

-- BOM (物料清单) 权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'bom:read', '查看BOM', 'BOM', 'VIEW', 'API', 1, 1),
(NULL, 'bom:create', '创建BOM', 'BOM', 'CREATE', 'API', 1, 1),
(NULL, 'bom:update', '编辑BOM', 'BOM', 'EDIT', 'API', 1, 1),
(NULL, 'bom:approve', '审批BOM', 'BOM', 'APPROVE', 'API', 1, 1);

-- 系统管理权限
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'admin:cache:clear', '清除缓存', 'ADMIN', 'EDIT', 'API', 1, 1),
(NULL, 'admin:cache:reset', '重置缓存', 'ADMIN', 'EDIT', 'API', 1, 1);

-- ============================================
-- 2. 兼容旧格式权限码（大写下划线格式映射到小写冒号格式）
--    在端点代码统一之前，需要同时支持两种格式
-- ============================================
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'USER_VIEW', '查看用户(兼容)', 'USER', 'VIEW', 'API', 1, 1),
(NULL, 'USER_CREATE', '创建用户(兼容)', 'USER', 'CREATE', 'API', 1, 1),
(NULL, 'USER_UPDATE', '编辑用户(兼容)', 'USER', 'UPDATE', 'API', 1, 1),
(NULL, 'USER_DELETE', '删除用户(兼容)', 'USER', 'DELETE', 'API', 1, 1),
(NULL, 'ROLE_VIEW', '查看角色(兼容)', 'ROLE', 'VIEW', 'API', 1, 1),
(NULL, 'AUDIT_VIEW', '查看审计日志(兼容)', 'AUDIT', 'VIEW', 'API', 1, 1);

-- ============================================
-- 3. 角色-权限映射
-- ============================================

-- ADMIN: 所有权限（系统管理员拥有全部权限）
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, ap.id
FROM roles r CROSS JOIN api_permissions ap
WHERE r.role_code = 'ADMIN' AND ap.is_active = 1;

-- GM（总经理）: 所有查看权限 + 审批权限
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, ap.id
FROM roles r JOIN api_permissions ap
WHERE r.role_code = 'GM' AND (
    ap.action = 'VIEW'
    OR ap.perm_code IN (
        'budget:approve',
        'business_support:approve',
        'report:read', 'report:export',
        'audit:view', 'AUDIT_VIEW'
    )
);

-- CTO（技术总监）: 项目、技术、工程师、研发相关
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, ap.id
FROM roles r JOIN api_permissions ap
WHERE r.role_code = 'CTO' AND (
    ap.module IN ('PROJECT', 'MACHINE', 'MILESTONE', 'ISSUE', 'TECHNICAL_SPEC', 'ENGINEER', 'RD_PROJECT', 'DOCUMENT')
    OR ap.perm_code IN (
        'project_evaluation:read', 'project_evaluation:create', 'project_evaluation:update',
        'project_role:read', 'project_role:create', 'project_role:assign',
        'staff_matching:read', 'staff_matching:create',
        'report:read', 'report:export',
        'task_center:read'
    )
);

-- CFO（财务总监）: 财务、成本、预算、报表
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, ap.id
FROM roles r JOIN api_permissions ap
WHERE r.role_code = 'CFO' AND (
    ap.module IN ('FINANCE', 'COST', 'BUDGET', 'HOURLY_RATE')
    OR ap.perm_code IN (
        'project:read', 'report:read', 'report:export',
        'budget:approve', 'procurement:read'
    )
);

-- SALES_DIR（销售总监）: 客户、销售、商务、报表
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, ap.id
FROM roles r JOIN api_permissions ap
WHERE r.role_code = 'SALES_DIR' AND (
    ap.module IN ('CUSTOMER', 'BUSINESS_SUPPORT', 'PRESALE', 'ADVANTAGE_PRODUCT')
    OR ap.perm_code IN (
        'project:read', 'report:read', 'report:export',
        'business_support:approve'
    )
);

-- PM（项目经理）: 项目全权管理
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, ap.id
FROM roles r JOIN api_permissions ap
WHERE r.role_code = 'PM' AND (
    ap.module IN ('PROJECT', 'MACHINE', 'MILESTONE', 'ISSUE', 'DOCUMENT',
                  'TASK_CENTER', 'PROJECT_EVAL', 'PROJECT_ROLE', 'ASSEMBLY_KIT',
                  'INSTALLATION', 'STAFF_MATCHING')
    OR ap.perm_code IN (
        'timesheet:read', 'timesheet:submit',
        'cost:read', 'procurement:read',
        'report:read', 'report:create',
        'work_log:config:read', 'work_log:config:create', 'work_log:config:update',
        'customer:read', 'supplier:read',
        'notification:read', 'notification:delete'
    )
);

-- PMC（计划管理）: 计划、物料、采购协调
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, ap.id
FROM roles r JOIN api_permissions ap
WHERE r.role_code = 'PMC' AND (
    ap.perm_code IN (
        'project:read', 'machine:read',
        'milestone:read', 'milestone:create', 'milestone:update',
        'assembly_kit:read', 'assembly_kit:create', 'assembly_kit:update',
        'procurement:read', 'supplier:read',
        'task_center:read', 'task_center:create', 'task_center:update', 'task_center:assign',
        'report:read',
        'notification:read', 'notification:delete'
    )
);

-- QA_MGR（质量主管）: 质量、验收、问题
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, ap.id
FROM roles r JOIN api_permissions ap
WHERE r.role_code = 'QA_MGR' AND (
    ap.module IN ('ISSUE')
    OR ap.perm_code IN (
        'project:read', 'machine:read', 'milestone:read',
        'document:read', 'document:create',
        'report:read',
        'project_evaluation:read', 'project_evaluation:create',
        'notification:read', 'notification:delete'
    )
);

-- PU_MGR（采购主管）: 采购、供应商、外协
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, ap.id
FROM roles r JOIN api_permissions ap
WHERE r.role_code = 'PU_MGR' AND (
    ap.module IN ('SUPPLIER', 'PROCUREMENT')
    OR ap.perm_code IN (
        'project:read', 'machine:read',
        'assembly_kit:read',
        'cost:read',
        'report:read',
        'notification:read', 'notification:delete'
    )
);

-- ME / EE / SW（工程师）: 项目执行、任务、工时
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, ap.id
FROM roles r JOIN api_permissions ap
WHERE r.role_code IN ('ME', 'EE', 'SW') AND (
    ap.perm_code IN (
        'project:read', 'machine:read',
        'milestone:read',
        'issue:read', 'issue:create', 'issue:update',
        'document:read', 'document:create',
        'timesheet:read', 'timesheet:create', 'timesheet:update', 'timesheet:delete', 'timesheet:submit',
        'task_center:read', 'task_center:update',
        'technical_spec:read', 'technical_spec:create', 'technical_spec:update',
        'assembly_kit:read',
        'notification:read', 'notification:delete'
    )
);

-- QA（质量工程师）: 检验、验收执行、问题
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, ap.id
FROM roles r JOIN api_permissions ap
WHERE r.role_code = 'QA' AND (
    ap.perm_code IN (
        'project:read', 'machine:read', 'milestone:read',
        'issue:read', 'issue:create', 'issue:update',
        'document:read', 'document:create',
        'timesheet:read', 'timesheet:create', 'timesheet:submit',
        'notification:read', 'notification:delete'
    )
);

-- PU（采购专员）: 采购执行
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, ap.id
FROM roles r JOIN api_permissions ap
WHERE r.role_code = 'PU' AND (
    ap.perm_code IN (
        'project:read', 'machine:read',
        'procurement:read', 'supplier:read',
        'assembly_kit:read',
        'notification:read', 'notification:delete'
    )
);

-- FI（财务专员）: 财务、成本、发票
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, ap.id
FROM roles r JOIN api_permissions ap
WHERE r.role_code = 'FI' AND (
    ap.perm_code IN (
        'project:read', 'finance:read', 'cost:read',
        'budget:read', 'hourly_rate:read',
        'procurement:read', 'customer:read',
        'report:read', 'report:export',
        'notification:read', 'notification:delete'
    )
);

-- SA（销售专员）: 客户、商机
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, ap.id
FROM roles r JOIN api_permissions ap
WHERE r.role_code = 'SA' AND (
    ap.perm_code IN (
        'customer:read', 'customer:create', 'customer:update',
        'project:read',
        'business_support:read', 'business_support:create', 'business_support:update',
        'presale_analytics:create',
        'advantage_product:read',
        'report:read',
        'notification:read', 'notification:delete'
    )
);

-- ASSEMBLER（装配技师）: 装配、工时
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, ap.id
FROM roles r JOIN api_permissions ap
WHERE r.role_code = 'ASSEMBLER' AND (
    ap.perm_code IN (
        'project:read', 'machine:read',
        'assembly_kit:read',
        'timesheet:read', 'timesheet:create', 'timesheet:submit',
        'issue:read', 'issue:create',
        'task_center:read', 'task_center:update',
        'notification:read', 'notification:delete'
    )
);

-- DEBUG（调试工程师）: 调试、问题记录
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, ap.id
FROM roles r JOIN api_permissions ap
WHERE r.role_code = 'DEBUG' AND (
    ap.perm_code IN (
        'project:read', 'machine:read',
        'issue:read', 'issue:create', 'issue:update',
        'timesheet:read', 'timesheet:create', 'timesheet:submit',
        'document:read', 'document:create',
        'task_center:read', 'task_center:update',
        'notification:read', 'notification:delete'
    )
);

-- CUSTOMER（客户）: 只读自己的项目
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, ap.id
FROM roles r JOIN api_permissions ap
WHERE r.role_code = 'CUSTOMER' AND (
    ap.perm_code IN (
        'project:read', 'machine:read', 'milestone:read',
        'notification:read'
    )
);

-- SUPPLIER（供应商）: 只读采购相关
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, ap.id
FROM roles r JOIN api_permissions ap
WHERE r.role_code = 'SUPPLIER' AND (
    ap.perm_code IN (
        'procurement:read',
        'notification:read'
    )
);
