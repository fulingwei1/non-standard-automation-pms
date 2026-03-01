/**
 * 权限检查函数
 * 提供采购、财务、生产、项目评审等模块的权限检查
 */

/**
 * 检查是否有采购模块访问权限
 * 包含齐套分析、物料分析等页面的访问权限
 */
export function hasProcurementAccess(role, isSuperuser = false) {
  if (isSuperuser) {return true;}

  const allowedRoles = [
    "admin",
    "super_admin",
    "chairman",
    "gm",
    // 采购部
    "procurement_manager",
    "procurement_engineer",
    "procurement",
    "buyer",
    // 项目管理
    "pmc",
    "pm",
    "project_dept_manager",
    "DEPT_MGR",
    // 生产制造
    "production_manager",
    "manufacturing_director",
    "production_director",
    // 中文角色名
    "采购部经理",
    "采购工程师",
    "采购专员",
    "采购员",
    "项目经理",
    "项目部经理",
    "生产部经理",
    "生产部总监",
    "制造总监",
    "计划管理",
    "PMC",
    "部门经理",
  ];

  return allowedRoles.includes(role);
}

/**
 * 检查是否有财务模块访问权限
 */
export function hasFinanceAccess(role, isSuperuser = false) {
  if (isSuperuser) {return true;}

  // 统一转换为字符串并转为小写进行比较（英文角色）
  const roleStr = String(role || "").trim();
  const roleLower = roleStr.toLowerCase();

  const allowedRoles = [
    "admin",
    "super_admin",
    "chairman",
    "gm",
    "finance_manager",
    "finance",
    "accountant",
    "sales_director",
    "sales_manager",
    "sales",
    "business_support",
    "presales_manager",
    "presales",
    "project_dept_manager",
    "pmc",
    "pm",
    "财务经理",
    "会计",
    "销售总监",
    "销售经理",
    "销售工程师",
    "商务支持",
    "商务支持专员",
    "售前经理",
    "售前技术工程师",
    "项目经理",
    "项目部经理",
    // 中文角色名（完整匹配）
    "总经理",
    "管理员",
    "系统管理员",
    "董事长",
    "财务人员",
  ];

  // 同时检查原始值、小写值和中文值
  return (
    allowedRoles.includes(roleStr) ||
    allowedRoles.includes(roleLower) ||
    allowedRoles.some((r) => r === roleStr)
  );
}

/**
 * 检查是否有生产模块访问权限
 * 包含装配齐套看板等页面的访问权限
 */
export function hasProductionAccess(role, isSuperuser = false) {
  if (isSuperuser) {return true;}

  const allowedRoles = [
    "admin",
    "super_admin",
    "chairman",
    "gm",
    // 生产制造
    "manufacturing_director",
    "production_manager",
    "production_director",
    "DEPT_MGR",
    // 项目管理
    "pmc",
    "pm",
    "project_dept_manager",
    // 装配人员
    "assembler",
    "assembler_mechanic",
    "assembler_electrician",
    // 中文角色名
    "制造总监",
    "生产部经理",
    "生产部总监",
    "项目经理",
    "项目部经理",
    "计划管理",
    "PMC",
    "部门经理",
    "装配技工",
    "装配钳工",
    "装配电工",
  ];

  return allowedRoles.includes(role);
}

/**
 * 检查是否有项目复盘访问权限
 * 优先使用权限代码检查（动态），角色检查作为兜底（兼容旧数据）
 * @param {string} role - 用户角色代码
 * @param {boolean} isSuperuser - 是否超级管理员
 * @param {string[]} permissions - 用户权限代码列表（可选，优先使用）
 */
export function hasProjectReviewAccess(role, isSuperuser = false, permissions = []) {
  // 超级管理员直接放行
  if (isSuperuser) {return true;}

  // 优先使用权限代码检查（推荐方式，从数据库动态获取）
  if (permissions && permissions.length > 0) {
    const requiredPermissions = [
      'project_review:read',
      'lessons_learned:read',
      'best_practice:read'
    ];
    // 只要有任一项目复盘相关权限即可访问
    return requiredPermissions.some(perm => permissions.includes(perm));
  }

  // 兜底：角色白名单（兼容旧系统，权限数据未迁移完成时使用）
  const allowedRoles = [
    "admin",
    "super_admin",
    "ADMIN",
    "chairman",
    "gm",
    "GM",
    "PMO_DIR",
    "project_dept_manager",
    "PROJECT_MANAGER",
    "pmc",
    "pm",
    "PM",
    "tech_dev_manager",
    "CTO",
    "me_dept_manager",
    "ME_MGR",
    "ee_dept_manager",
    "EE_MGR",
    "te_dept_manager",
    "VP",
    "PRODUCTION_DIR",
  ];

  return allowedRoles.includes(role);
}

/**
 * 检查是否有战略管理模块访问权限
 * 战略管理模块包含：战略仪表板、CSF/KPI管理、战略分解、战略审视等
 *
 * 访问级别：
 * - 完整访问：高管层、系统管理员
 * - 部门访问：部门经理（查看部门目标）
 * - 个人访问：普通员工（仅查看个人KPI）
 *
 * @param {string} role - 用户角色代码
 * @param {boolean} isSuperuser - 是否超级管理员
 * @param {string[]} permissions - 用户权限代码列表（可选）
 */
