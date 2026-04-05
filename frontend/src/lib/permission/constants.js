/**
 * 权限常量 - 模块级权限码
 *
 * 所有模块访问权限统一用 `module:access` 格式，
 * 后端在分配角色权限时自动包含对应模块的 access 权限。
 *
 * 旧的 hasProcurementAccess(role) 等角色白名单函数已废弃，
 * 统一通过 hasModuleAccess('procurement') 或
 * hasPermission('purchase:read') 进行权限检查。
 */

/**
 * 模块访问权限码映射
 * key: 前端模块标识
 * value: 后端权限码数组（任一匹配即有访问权限）
 */
export const MODULE_PERMISSIONS = {
  procurement: [
    'purchase:read',
    'purchase:create',
    'purchase:request:read',
    'purchase:receipt:read',
    'purchase:analysis:read',
    'material:read',
    'material:demand:read',
    'material:requisition:read',
    'supplier:read',
    'bom:read',
  ],
  finance: [
    'finance:receivable:read',
    'finance:invoice:read',
    'finance:report:read',
    'payment:approve',
    'cost:accounting:read',
    'settlement:read',
  ],
  production: [
    'production:board:read',
    'production:plan:read',
    'production:exception:read',
    'workorder:read',
    'dispatch:read',
  ],
  project_review: [
    'project_review:read',
    'lessons_learned:read',
    'best_practice:read',
  ],
  strategy: [
    'strategy:read',
    'strategy:write',
    'strategy:admin',
    'kpi:read',
    'kpi:write',
    'personal_kpi:read',
  ],
  warehouse: [
    'warehouse:read',
    'warehouse:manage',
    'warehouse:inventory:read',
  ],
  quality: [
    'quality:read',
    'quality:manage',
    'quality:inspection:read',
  ],
  project: [
    'project:project:read',
    'project:project:create',
    'project:initiation:read',
  ],
  sales: [
    'sales:lead:read',
    'sales:opportunity:read',
    'sales:quote:read',
    'sales:contract:read',
    'sales:funnel:read',
    'sales:target:read',
  ],
};

/**
 * 模块中文名称（用于无权限提示）
 */
export const MODULE_LABELS = {
  procurement: '采购和物料管理',
  finance: '财务管理',
  production: '生产管理',
  project_review: '项目复盘',
  strategy: '战略管理',
  warehouse: '仓储管理',
  quality: '质量管理',
  project: '项目管理',
  sales: '销售管理',
};
