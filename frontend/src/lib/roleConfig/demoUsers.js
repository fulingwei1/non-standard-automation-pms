/**
 * 演示账户配置
 * 包含所有角色的演示用户信息
 */

export const DEMO_USERS = {
  // 管理层
  chairman: {
    username: "chairman",
    name: "王董事长",
    role: "chairman",
    department: "董事会",
    is_superuser: false,
  },
  gm: {
    username: "gm",
    name: "李总经理",
    role: "gm",
    department: "总经办",
    is_superuser: false,
  },
  super_admin: {
    username: "super_admin",
    name: "系统管理员",
    role: "super_admin",
    department: "信息部",
    is_superuser: true,
  },
  admin: {
    username: "admin",
    name: "管理员",
    role: "admin",
    department: "信息部",
    is_superuser: true,
  },

  // 销售系统
  sales_director: {
    username: "sales_director",
    name: "张销售总监",
    role: "sales_director",
    department: "销售部",
    is_superuser: false,
  },
  sales_manager: {
    username: "sales_manager",
    name: "刘销售经理",
    role: "sales_manager",
    department: "销售部",
    is_superuser: false,
  },
  sales: {
    username: "sales",
    name: "销售小王",
    role: "sales",
    department: "销售部",
    is_superuser: false,
  },
  presales_manager: {
    username: "presales_manager",
    name: "售前经理",
    role: "presales_manager",
    department: "售前部",
    is_superuser: false,
  },
  presales: {
    username: "presales",
    name: "售前工程师",
    role: "presales",
    department: "售前部",
    is_superuser: false,
  },
  business_support: {
    username: "business_support",
    name: "商务支持",
    role: "business_support",
    department: "销售部",
    is_superuser: false,
  },

  // 项目管理
  project_dept_manager: {
    username: "project_dept_manager",
    name: "项目部经理",
    role: "project_dept_manager",
    department: "项目部",
    is_superuser: false,
  },
  demo_pm_liu: {
    username: "demo_pm_liu",
    name: "刘项目经理",
    role: "pmc",
    department: "项目部",
    is_superuser: false,
  },
  pmc: {
    username: "pmc",
    name: "项目经理",
    role: "pmc",
    department: "项目部",
    is_superuser: false,
  },

  // 工程技术中心
  tech_dev_manager: {
    username: "tech_dev_manager",
    name: "技术开发部经理",
    role: "tech_dev_manager",
    department: "技术开发部",
    is_superuser: false,
  },
  rd_engineer: {
    username: "rd_engineer",
    name: "研发工程师",
    role: "rd_engineer",
    department: "技术开发部",
    is_superuser: false,
  },
  me_dept_manager: {
    username: "me_dept_manager",
    name: "机械部经理",
    role: "me_dept_manager",
    department: "机械部",
    is_superuser: false,
  },
  te_dept_manager: {
    username: "te_dept_manager",
    name: "测试部经理",
    role: "te_dept_manager",
    department: "测试部",
    is_superuser: false,
  },
  ee_dept_manager: {
    username: "ee_dept_manager",
    name: "电气部经理",
    role: "ee_dept_manager",
    department: "电气部",
    is_superuser: false,
  },
  me_engineer: {
    username: "me_engineer",
    name: "机械工程师",
    role: "me_engineer",
    department: "机械部",
    is_superuser: false,
  },
  te_engineer: {
    username: "te_engineer",
    name: "测试工程师",
    role: "te_engineer",
    department: "测试部",
    is_superuser: false,
  },
  ee_engineer: {
    username: "ee_engineer",
    name: "电气工程师",
    role: "ee_engineer",
    department: "电气部",
    is_superuser: false,
  },

  // 采购部
  procurement_manager: {
    username: "procurement_manager",
    name: "采购部经理",
    role: "procurement_manager",
    department: "采购部",
    is_superuser: false,
  },
  procurement_engineer: {
    username: "procurement_engineer",
    name: "采购工程师",
    role: "procurement_engineer",
    department: "采购部",
    is_superuser: false,
  },

  // 制造中心
  manufacturing_director: {
    username: "manufacturing_director",
    name: "制造总监",
    role: "manufacturing_director",
    department: "制造中心",
    is_superuser: false,
  },
  production_manager: {
    username: "production_manager",
    name: "生产部经理",
    role: "production_manager",
    department: "生产部",
    is_superuser: false,
  },
  assembler_mechanic: {
    username: "assembler_mechanic",
    name: "装配钳工",
    role: "assembler_mechanic",
    department: "生产部",
    is_superuser: false,
  },
  assembler_electrician: {
    username: "assembler_electrician",
    name: "装配电工",
    role: "assembler_electrician",
    department: "生产部",
    is_superuser: false,
  },
  customer_service_manager: {
    username: "customer_service_manager",
    name: "客服部经理",
    role: "customer_service_manager",
    department: "客服部",
    is_superuser: false,
  },
  customer_service_engineer: {
    username: "customer_service_engineer",
    name: "客服工程师",
    role: "customer_service_engineer",
    department: "客服部",
    is_superuser: false,
  },

  // 后台支持
  finance_manager: {
    username: "finance_manager",
    name: "财务经理",
    role: "finance_manager",
    department: "财务部",
    is_superuser: false,
  },
  hr_manager: {
    username: "hr_manager",
    name: "人事经理",
    role: "hr_manager",
    department: "人力资源部",
    is_superuser: false,
  },
};
