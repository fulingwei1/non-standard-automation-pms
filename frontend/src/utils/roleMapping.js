/**
 * 角色名称 → 前端角色代码映射
 *
 * 支持中英文精确匹配 + 关键词模糊匹配
 */

const ROLE_MAP = {
  "系统管理员": "admin",
  ADMIN: "admin",
  Administrator: "admin",
  SUPER_ADMIN: "super_admin",
  SuperAdmin: "super_admin",
  总经理: "gm",
  GM: "gm",
  GeneralManager: "gm",
  常务副总: "vice_chairman",
  副总经理: "vice_chairman",
  董秘: "dongmi",
  董事长: "chairman",
  Chairman: "chairman",
  项目经理: "pm",
  PM: "pm",
  ProjectManager: "pm",
  项目管理部总监: "project_dept_manager",
  PMC: "pmc",
  PMC主管: "pmc",
  销售总监: "sales_director",
  SALES_DIR: "sales_director",
  SalesDirector: "sales_director",
  营销中心总监: "sales_director",
  销售经理: "sales_manager",
  SalesManager: "sales_manager",
  销售工程师: "sales",
  SalesEngineer: "sales",
  生产部经理: "production_manager",
  电机生产部经理: "production_manager",
  ProductionManager: "production_manager",
  PRODUCTION_MANAGER: "production_manager",
  制造总监: "manufacturing_director",
  ManufacturingDirector: "manufacturing_director",
  MANUFACTURING_DIRECTOR: "manufacturing_director",
  计划管理: "pmc",
  采购部经理: "procurement_manager",
  采购经理: "procurement_manager",
  ProcurementManager: "procurement_manager",
  PROCUREMENT_MANAGER: "procurement_manager",
  采购工程师: "procurement_engineer",
  ProcurementEngineer: "procurement_engineer",
  PROCUREMENT_ENGINEER: "procurement_engineer",
  采购员: "buyer",
  Buyer: "buyer",
  BUYER: "buyer",
  客服主管: "customer_service_manager",
  CustomerServiceManager: "customer_service_manager",
};

// 关键词模糊匹配规则（按优先级排序）
const KEYWORD_RULES = [
  { test: (n) => n.includes("董事长"), role: "chairman" },
  { test: (n) => n.includes("常务") && n.includes("副总"), role: "vice_chairman" },
  { test: (n) => n.includes("总经理") && n.includes("副"), role: "vice_chairman" },
  { test: (n) => n.includes("董秘"), role: "dongmi" },
  { test: (n) => n.includes("总经理") || n.includes("GeneralManager") || n === "GM", role: "gm" },
  { test: (n) => n.includes("生产") && !n.includes("制造"), role: "production_manager" },
  { test: (n) => n.includes("制造") && n.includes("总监"), role: "manufacturing_director" },
  { test: (n) => n.includes("采购") && (n.includes("经理") || n.includes("Manager")), role: "procurement_manager" },
  { test: (n) => n.includes("采购") && (n.includes("工程师") || n.includes("Engineer")), role: "procurement_engineer" },
  { test: (n) => n.includes("采购") && n.includes("员"), role: "buyer" },
];

/**
 * 将角色名称/对象解析为前端角色代码
 * @param {string|object} role - 角色名称字符串或角色对象
 * @returns {string} 前端角色代码
 */
export function resolveRoleCode(role) {
  const roleName = typeof role === "object"
    ? (role.role_code || role.role_name || String(role))
    : String(role);

  // 1. 精确匹配
  if (ROLE_MAP[roleName]) return ROLE_MAP[roleName];

  // 2. 忽略大小写匹配
  const lowerName = roleName.toLowerCase();
  const caseMatch = Object.keys(ROLE_MAP).find(
    (key) => key.toLowerCase() === lowerName
  );
  if (caseMatch) return ROLE_MAP[caseMatch];

  // 3. 关键词模糊匹配
  const keywordMatch = KEYWORD_RULES.find((rule) => rule.test(roleName));
  if (keywordMatch) return keywordMatch.role;

  // 4. 回退：转下划线格式
  return roleName.toLowerCase().replace(/\s+/g, "_").replace(/-/g, "_");
}
