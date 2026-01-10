/**
 * 角色到仪表板路径的映射配置
 */
export const roleDashboardMap = {
  // 管理层
  chairman: "/chairman-dashboard",
  gm: "/gm-dashboard",
  admin: "/admin-dashboard",
  super_admin: "/admin-dashboard",

  // 销售/支持
  sales_director: "/sales-director-dashboard",
  sales_manager: "/sales-manager-dashboard",
  sales: "/sales-dashboard",
  business_support: "/business-support",
  presales: "/presales-dashboard",
  presales_manager: "/presales-manager-dashboard",

  // 项目管理
  project_dept_manager: "/pmo/dashboard",
  pm: "/pmo/dashboard",
  pmc: "/pmo/dashboard",

  // 工程技术中心
  tech_dev_manager: "/workstation",
  rd_engineer: "/workstation",
  me_dept_manager: "/workstation",
  te_dept_manager: "/workstation",
  ee_dept_manager: "/workstation",
  me_engineer: "/workstation",
  te_engineer: "/workstation",
  ee_engineer: "/workstation",
  sw_engineer: "/workstation",

  // 采购部
  procurement_manager: "/procurement-manager-dashboard",
  procurement_engineer: "/procurement-dashboard",

  // 制造中心
  manufacturing_director: "/manufacturing-director-dashboard",
  production_manager: "/production-dashboard",
  assembler: "/assembly-tasks",
  assembler_mechanic: "/assembly-tasks",
  assembler_electrician: "/assembly-tasks",

  // 客户服务
  customer_service_engineer: "/customer-service-dashboard",
  customer_service_manager: "/customer-service-dashboard",

  // 后台支持
  finance_manager: "/finance-manager-dashboard",
  hr_manager: "/hr-manager-dashboard",
  administrative_manager: "/administrative-dashboard",
};
