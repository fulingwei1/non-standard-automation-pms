/**
 * 战略模块访问权限
 * 提供战略模块的权限检查和访问级别
 */

export function hasStrategyAccess(role, isSuperuser = false, permissions = []) {
  // 超级管理员直接放行
  if (isSuperuser) return true;

  // 优先使用权限代码检查
  if (permissions && permissions.length > 0) {
    const strategyPermissions = [
      'strategy:read',
      'strategy:write',
      'strategy:admin',
      'kpi:read',
      'kpi:write',
      'personal_kpi:read',
    ];
    if (strategyPermissions.some(perm => permissions.includes(perm))) {
      return true;
    }
  }

  // 角色白名单
  const allowedRoles = [
    // 系统管理员
    "admin",
    "super_admin",
    "ADMIN",
    // 高管层 - 完整访问
    "chairman",
    "gm",
    "GM",
    "vp",
    "VP",
    // PMO - 战略执行监控
    "PMO_DIR",
    "project_dept_manager",
    "pmc",
    "pm",
    // 部门经理 - 部门目标管理
    "sales_director",
    "sales_manager",
    "tech_dev_manager",
    "me_dept_manager",
    "ee_dept_manager",
    "te_dept_manager",
    "procurement_manager",
    "production_manager",
    "manufacturing_director",
    "production_director",
    "customer_service_manager",
    "finance_manager",
    "hr_manager",
    "presales_manager",
    // 中文角色名
    "董事长",
    "总经理",
    "副总经理",
    "管理员",
    "系统管理员",
    "项目管理部总监",
    "项目部经理",
    "项目经理",
    "销售总监",
    "销售经理",
    "技术开发部经理",
    "机械部经理",
    "电气部经理",
    "测试部经理",
    "采购部经理",
    "生产部经理",
    "生产部总监",
    "制造总监",
    "客服部经理",
    "财务经理",
    "人事经理",
    "售前经理",
  ];

  return allowedRoles.includes(role);
}

/**
 * 检查战略模块的访问级别
 * @param {string} role - 用户角色代码
 * @param {boolean} isSuperuser - 是否超级管理员
 * @returns {'full' | 'department' | 'personal' | 'none'} 访问级别
 */
export function getStrategyAccessLevel(role, isSuperuser = false) {
  if (isSuperuser) return 'full';

  // 完整访问 - 高管层
  const fullAccessRoles = [
    "admin", "super_admin", "chairman", "gm", "vp", "VP",
    "PMO_DIR", "hr_manager",
    "董事长", "总经理", "副总经理", "管理员", "人事经理",
  ];
  if (fullAccessRoles.includes(role)) return 'full';

  // 部门访问 - 部门经理
  const deptAccessRoles = [
    "project_dept_manager", "sales_director", "sales_manager",
    "tech_dev_manager", "me_dept_manager", "ee_dept_manager", "te_dept_manager",
    "procurement_manager", "production_manager", "manufacturing_director",
    "production_director", "customer_service_manager", "finance_manager",
    "presales_manager", "pmc", "pm",
  ];
  if (deptAccessRoles.includes(role)) return 'department';

  // 个人访问 - 普通员工（暂时不开放，后续可以开放个人KPI查看）
  // return 'personal';

  return 'none';
}

/**
 * 检查是否是工程师角色
 */
