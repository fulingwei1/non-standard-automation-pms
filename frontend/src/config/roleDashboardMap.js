/**
 * 角色到工作台路径的映射配置
 *
 * 统一使用数据库 roles.role_code 作为键
 *
 * 工作台分类：
 * - /workstation/sales - 销售工作台
 * - /workstation/project - 项目工作台
 * - /workstation/engineering - 工程技术工作台
 * - /workstation/production - 生产工作台
 * - /workstation/procurement - 采购工作台
 * - /workstation/quality - 质量工作台
 * - /workstation/warehouse - 仓储工作台
 * - /workstation/management - 管理工作台（高管、管理员、财务等）
 * - /workstation/service - 服务工作台（客户、供应商、客服）
 */

/**
 * 角色工作台映射
 *
 * 键：数据库 roles.role_code（大写）
 * 值：工作台路径
 */
export const roleDashboardMap = {
  // ============================================
  // 系统角色 (Level 0)
  // ============================================
  'ADMIN': '/workstation/management',          // 系统管理员

  // ============================================
  // 管理层角色 (Level 1)
  // ============================================
  'GM': '/workstation/management',             // 总经理
  'CFO': '/workstation/management',            // 财务总监
  'CTO': '/workstation/management',            // 技术总监
  'SALES_DIR': '/workstation/sales',           // 销售总监

  // ============================================
  // 主管级角色 (Level 2)
  // ============================================
  'PM': '/workstation/project',                // 项目经理
  'PMC': '/workstation/project',               // 计划管理
  'QA_MGR': '/workstation/quality',            // 质量主管
  'PU_MGR': '/workstation/procurement',        // 采购主管

  // ============================================
  // 专员级角色 (Level 3)
  // ============================================
  // 工程技术
  'ME': '/workstation/engineering',            // 机械工程师
  'EE': '/workstation/engineering',            // 电气工程师
  'SW': '/workstation/engineering',            // 软件工程师
  'DEBUG': '/workstation/engineering',         // 调试工程师

  // 质量
  'QA': '/workstation/quality',                // 质量工程师

  // 采购
  'PU': '/workstation/procurement',            // 采购专员

  // 财务
  'FI': '/workstation/management',             // 财务专员

  // 销售
  'SA': '/workstation/sales',                  // 销售专员

  // 生产
  'ASSEMBLER': '/workstation/production',      // 装配技师

  // ============================================
  // 外部角色 (Level 4)
  // ============================================
  'CUSTOMER': '/workstation/service',          // 客户
  'SUPPLIER': '/workstation/service',          // 供应商

  // ============================================
  // 扩展角色 (2026-01-22 新增)
  // ============================================

  // 高管扩展
  'CHAIRMAN': '/workstation/management',      // 董事长
  'VICE_CHAIRMAN': '/workstation/management', // 副总经理
  'DONGMI': '/workstation/management',        // 董秘

  // 售前
  'PRESALES': '/workstation/presales',        // 售前工程师
  'PRESALES_MGR': '/workstation/presales',    // 售前经理
  'BUSINESS_SUPPORT': '/workstation/presales', // 商务支持

  // 客服
  'CUSTOMER_SERVICE': '/workstation/service', // 客服工程师
  'CUSTOMER_SERVICE_MGR': '/workstation/service', // 客服经理

  // HR
  'HR': '/workstation/management',            // HR专员
  'HR_MGR': '/workstation/management',        // HR经理

  // 仓储
  'WAREHOUSE': '/workstation/warehouse',      // 仓储管理员
  'WAREHOUSE_MGR': '/workstation/warehouse',  // 仓储经理

  // 生产管理扩展
  'PRODUCTION_MGR': '/workstation/production', // 生产经理
  'MANUFACTURING_DIR': '/workstation/production', // 制造总监
};

/**
 * 前端旧格式到数据库新格式的映射表
 * 用于兼容 Login.jsx 中使用的下划线小写格式
 */
const legacyRoleMap = {
  // 原有角色映射
  'sales_director': 'SALES_DIR',
  'sales_manager': 'SALES_DIR',
  'sales': 'SA',
  'procurement_manager': 'PU_MGR',
  'procurement_engineer': 'PU',
  'buyer': 'PU',

  // 新增角色映射 (2026-01-22)
  'chairman': 'CHAIRMAN',
  'vice_chairman': 'VICE_CHAIRMAN',
  'dongmi': 'DONGMI',
  'presales': 'PRESALES',
  'presales_manager': 'PRESALES_MGR',
  'presales_mgr': 'PRESALES_MGR',
  'business_support': 'BUSINESS_SUPPORT',
  'customer_service': 'CUSTOMER_SERVICE',
  'customer_service_manager': 'CUSTOMER_SERVICE_MGR',
  'customer_service_mgr': 'CUSTOMER_SERVICE_MGR',
  'hr_manager': 'HR_MGR',
  'hr_mgr': 'HR_MGR',
  'warehouse_manager': 'WAREHOUSE_MGR',
  'warehouse_mgr': 'WAREHOUSE_MGR',
  'manufacturing_director': 'MANUFACTURING_DIR',
  'manufacturing_dir': 'MANUFACTURING_DIR',
  'production_manager': 'PRODUCTION_MGR',
  'production_mgr': 'PRODUCTION_MGR',
};

/**
 * 获取角色的工作台路径
 * @param {string} roleCode - 角色码（支持多种格式：'GM', 'gm', 'sales_director'）
 * @returns {string|null} 工作台路径，如果角色不存在返回 null
 */
export function getWorkstationPath(roleCode) {
  if (!roleCode) return null;

  // 1. 先尝试直接匹配（数据库大写格式）
  const upperCode = roleCode.toUpperCase();
  if (roleDashboardMap[upperCode]) {
    return roleDashboardMap[upperCode];
  }

  // 2. 尝试从旧格式映射表查找
  if (legacyRoleMap[roleCode.toLowerCase()]) {
    const dbRoleCode = legacyRoleMap[roleCode.toLowerCase()];
    return roleDashboardMap[dbRoleCode] || null;
  }

  // 3. 尝试小写直接匹配
  const lowerCode = roleCode.toLowerCase();
  if (roleDashboardMap[lowerCode]) {
    return roleDashboardMap[lowerCode];
  }

  return null;
}

/**
 * 获取工作台对应的所有角色码
 * @param {string} workstationPath - 工作台路径
 * @returns {string[]} 角色码数组
 */
export function getRolesForWorkstation(workstationPath) {
  return Object.entries(roleDashboardMap)
    .filter(([, path]) => path === workstationPath)
    .map(([roleCode]) => roleCode);
}

/**
 * 获取所有工作台路径
 * @returns {string[]} 工作台路径数组（去重）
 */
export function getAllWorkstationPaths() {
  return [...new Set(Object.values(roleDashboardMap))];
}

export default roleDashboardMap;
