/**
 * 角色信息配置
 * 包含角色定义和基础查询函数
 */

// 角色信息配置
export const ROLE_INFO = {
  // 管理层
  chairman: { name: "董事长", dataScope: "ALL", level: 1 },
  gm: { name: "总经理", dataScope: "ALL", level: 2 },
  vp: { name: "副总经理", dataScope: "ALL", level: 2 },
  VP: { name: "副总经理", dataScope: "ALL", level: 2 },
  vice_chairman: { name: "副总经理", dataScope: "ALL", level: 2 },
  VICE_CHAIRMAN: { name: "副总经理", dataScope: "ALL", level: 2 },
  admin: { name: "系统管理员", dataScope: "ALL", level: 2 },
  super_admin: { name: "超级管理员", dataScope: "ALL", level: 1 },

  // 销售系统
  sales_director: { name: "销售总监", dataScope: "DEPT", level: 3 },
  sales_manager: { name: "销售经理", dataScope: "DEPT", level: 4 },
  sales: { name: "销售工程师", dataScope: "OWN", level: 5 },
  presales_manager: { name: "售前经理", dataScope: "DEPT", level: 4 },
  presales: { name: "售前技术工程师", dataScope: "OWN", level: 5 },
  business_support: { name: "商务支持专员", dataScope: "OWN", level: 5 },

  // 项目管理
  PMO_DIR: { name: "项目管理部总监", dataScope: "DEPT", level: 3 },
  project_dept_manager: { name: "项目部经理", dataScope: "DEPT", level: 3 },
  pmc: { name: "项目经理(PMC)", dataScope: "OWN", level: 4 },
  pm: { name: "项目经理", dataScope: "OWN", level: 4 },

  // 工程技术中心
  tech_dev_manager: { name: "技术开发部经理", dataScope: "DEPT", level: 3 },
  me_dept_manager: { name: "机械部经理", dataScope: "DEPT", level: 3 },
  ee_dept_manager: { name: "电气部经理", dataScope: "DEPT", level: 3 },
  te_dept_manager: { name: "测试部经理", dataScope: "DEPT", level: 3 },
  rd_engineer: { name: "研发工程师", dataScope: "OWN", level: 5 },
  me_engineer: { name: "机械工程师", dataScope: "OWN", level: 5 },
  ee_engineer: { name: "电气工程师", dataScope: "OWN", level: 5 },
  sw_engineer: { name: "软件工程师", dataScope: "OWN", level: 5 },
  te_engineer: { name: "测试工程师", dataScope: "OWN", level: 5 },
  me_leader: { name: "机械组长", dataScope: "TEAM", level: 4 },
  ee_leader: { name: "电气组长", dataScope: "TEAM", level: 4 },
  te_leader: { name: "测试组长", dataScope: "TEAM", level: 4 },

  // 采购部
  procurement_manager: { name: "采购部经理", dataScope: "DEPT", level: 3 },
  procurement_engineer: { name: "采购工程师", dataScope: "OWN", level: 5 },
  procurement: { name: "采购专员", dataScope: "OWN", level: 5 },
  buyer: { name: "采购员", dataScope: "OWN", level: 5 },

  // 制造中心
  manufacturing_director: { name: "制造总监", dataScope: "DEPT", level: 2 },
  production_director: { name: "生产部总监", dataScope: "DEPT", level: 2 },
  production_manager: { name: "生产部经理", dataScope: "DEPT", level: 3 },
  assembler: { name: "装配技工", dataScope: "OWN", level: 6 },
  assembler_mechanic: { name: "装配钳工", dataScope: "OWN", level: 6 },
  assembler_electrician: { name: "装配电工", dataScope: "OWN", level: 6 },

  // 客服
  customer_service_manager: { name: "客服部经理", dataScope: "DEPT", level: 3 },
  customer_service_engineer: { name: "客服工程师", dataScope: "OWN", level: 5 },

  // 后台支持
  finance_manager: { name: "财务经理", dataScope: "ALL", level: 3 },
  hr_manager: { name: "人事经理", dataScope: "ALL", level: 3 },

  // 默认
  user: { name: "普通用户", dataScope: "OWN", level: 6 },
  unknown: { name: "角色错误", dataScope: "NONE", level: 99 },
};

/**
 * 获取角色信息
 * @param {string} role 角色代码
 * @returns {object} 角色信息 { name, dataScope, level }
 */
export function getRoleInfo(role) {
  if (role === null || role === undefined) {
    return ROLE_INFO.unknown;
  }

  const roleText = String(role).trim();
  if (!roleText) {
    return ROLE_INFO.unknown;
  }

  // 直接匹配
  if (ROLE_INFO[roleText]) {
    return ROLE_INFO[roleText];
  }

  // 尝试小写匹配
  const lowerRole = roleText.toLowerCase();
  if (ROLE_INFO[lowerRole]) {
    return ROLE_INFO[lowerRole];
  }

  // 中文角色名称映射
  const chineseMap = {
    董事长: "chairman",
    总经理: "gm",
    副总经理: "vice_chairman",
    普通用户: "user",
    系统管理员: "admin",
    超级管理员: "super_admin",
    管理员: "admin",
    销售总监: "sales_director",
    销售经理: "sales_manager",
    销售工程师: "sales",
    售前经理: "presales_manager",
    售前技术工程师: "presales",
    商务支持: "business_support",
    商务支持专员: "business_support",
    项目管理部总监: "PMO_DIR",
    项目部经理: "project_dept_manager",
    项目经理: "pmc",
    计划管理: "pmc",
    PMC: "pmc",
    技术开发部经理: "tech_dev_manager",
    机械部经理: "me_dept_manager",
    电气部经理: "ee_dept_manager",
    测试部经理: "te_dept_manager",
    研发工程师: "rd_engineer",
    机械工程师: "me_engineer",
    电气工程师: "ee_engineer",
    软件工程师: "sw_engineer",
    测试工程师: "te_engineer",
    采购部经理: "procurement_manager",
    采购经理: "procurement_manager",
    采购工程师: "procurement_engineer",
    采购专员: "procurement",
    采购员: "buyer",
    制造总监: "manufacturing_director",
    生产部总监: "production_director",
    生产部经理: "production_manager",
    装配技工: "assembler",
    装配钳工: "assembler_mechanic",
    装配电工: "assembler_electrician",
    客服部经理: "customer_service_manager",
    客服工程师: "customer_service_engineer",
    财务经理: "finance_manager",
    人事经理: "hr_manager",
  };

  if (chineseMap[roleText]) {
    return ROLE_INFO[chineseMap[roleText]];
  }

  // 关键词匹配（处理带描述的角色名称）
  if (roleText.includes("副总经理")) {
    return ROLE_INFO.vice_chairman;
  }

  return ROLE_INFO.unknown;
}
