/**
 * 角色工具函数
 * 提供角色类型判断等工具函数
 */

export function isEngineerRole(role) {
  const engineerRoles = [
    "me_engineer",
    "ee_engineer",
    "sw_engineer",
    "te_engineer",
    "rd_engineer",
    "me_leader",
    "ee_leader",
    "te_leader",
    "procurement_engineer",
    "customer_service_engineer",
    "机械工程师",
    "电气工程师",
    "软件工程师",
    "测试工程师",
    "研发工程师",
    "采购工程师",
    "客服工程师",
  ];

  return engineerRoles.includes(role);
}

/**
 * 检查是否是管理层角色
 */
export function isManagerRole(role) {
  const managerRoles = [
    "chairman",
    "gm",
    "admin",
    "super_admin",
    "sales_director",
    "sales_manager",
    "project_dept_manager",
    "tech_dev_manager",
    "me_dept_manager",
    "ee_dept_manager",
    "te_dept_manager",
    "procurement_manager",
    "production_manager",
    "manufacturing_director",
    "finance_manager",
    "hr_manager",
    "customer_service_manager",
    "董事长",
    "总经理",
    "管理员",
  ];

  return managerRoles.includes(role);
}
