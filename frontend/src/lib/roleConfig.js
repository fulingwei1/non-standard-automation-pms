/**
 * 角色配置文件
 * 包含演示账户、角色信息、权限检查等配置
 */

// 角色信息配置
export const ROLE_INFO = {
  // 管理层
  chairman: { name: "董事长", dataScope: "ALL", level: 1 },
  gm: { name: "总经理", dataScope: "ALL", level: 2 },
  vp: { name: "副总经理", dataScope: "ALL", level: 2 },
  VP: { name: "副总经理", dataScope: "ALL", level: 2 },
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
};

// 演示账户配置
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

/**
 * 获取角色信息
 * @param {string} role 角色代码
 * @returns {object} 角色信息 { name, dataScope, level }
 */
export function getRoleInfo(role) {
  if (!role) {
    return ROLE_INFO.user;
  }

  // 直接匹配
  if (ROLE_INFO[role]) {
    return ROLE_INFO[role];
  }

  // 尝试小写匹配
  const lowerRole = role.toLowerCase();
  if (ROLE_INFO[lowerRole]) {
    return ROLE_INFO[lowerRole];
  }

  // 中文角色名称映射
  const chineseMap = {
    董事长: "chairman",
    总经理: "gm",
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

  if (chineseMap[role]) {
    return ROLE_INFO[chineseMap[role]];
  }

  return ROLE_INFO.user;
}

/**
 * 获取角色的默认导航菜单
 * @param {string} role 角色代码
 * @returns {array} 导航组配置
 */
export function getNavForRole(role) {
  const navConfigs = {
    chairman: [
      {
        label: "战略决策",
        items: [
          {
            name: "董事长工作台",
            path: "/chairman-dashboard",
            icon: "LayoutDashboard",
          },
          { name: "战略分析", path: "/strategy-analysis", icon: "Target" },
        ],
      },
      {
        label: "全面监控",
        items: [
          { name: "项目看板", path: "/board", icon: "Kanban" },
          { name: "项目列表", path: "/projects", icon: "Briefcase" },
          { name: "运营大屏", path: "/operation", icon: "BarChart3" },
        ],
      },
      {
        label: "人员管理",
        items: [
          { name: "工程师绩效排名", path: "/engineer-performance/ranking", icon: "TrendingUp" },
        ],
      },
      {
        label: "重大事项",
        items: [
          { name: "审批中心", path: "/approvals", icon: "ClipboardCheck" },
          { name: "预警中心", path: "/alerts", icon: "AlertTriangle" },
        ],
      },
      {
        label: "个人中心",
        items: [
          { name: "通知中心", path: "/notifications", icon: "Bell" },
          { name: "知识管理", path: "/knowledge-base", icon: "BookOpen" },
          { name: "个人设置", path: "/settings", icon: "Settings" },
        ],
      },
    ],
    gm: [
      {
        label: "经营管理",
        items: [
          {
            name: "总经理工作台",
            path: "/gm-dashboard",
            icon: "LayoutDashboard",
          },
          { name: "运营大屏", path: "/operation", icon: "BarChart3" },
        ],
      },
      {
        label: "项目管理",
        items: [
          { name: "项目看板", path: "/board", icon: "Kanban" },
          { name: "项目列表", path: "/projects", icon: "Briefcase" },
          { name: "排期看板", path: "/schedule", icon: "Calendar" },
        ],
      },
      {
        label: "人员管理",
        items: [
          { name: "工程师绩效排名", path: "/engineer-performance/ranking", icon: "TrendingUp" },
        ],
      },
      {
        label: "审批与监控",
        items: [
          { name: "审批中心", path: "/approvals", icon: "ClipboardCheck" },
          { name: "预警中心", path: "/alerts", icon: "AlertTriangle" },
        ],
      },
      {
        label: "个人中心",
        items: [
          { name: "通知中心", path: "/notifications", icon: "Bell" },
          { name: "知识管理", path: "/knowledge-base", icon: "BookOpen" },
          { name: "个人设置", path: "/settings", icon: "Settings" },
        ],
      },
    ],
    VP: [
      {
        label: "经营管理",
        items: [
          {
            name: "副总工作台",
            path: "/gm-dashboard",
            icon: "LayoutDashboard",
          },
          { name: "运营大屏", path: "/operation", icon: "BarChart3" },
        ],
      },
      {
        label: "项目管理",
        items: [
          { name: "项目看板", path: "/board", icon: "Kanban" },
          { name: "项目列表", path: "/projects", icon: "Briefcase" },
          { name: "排期看板", path: "/schedule", icon: "Calendar" },
        ],
      },
      {
        label: "人员管理",
        items: [
          { name: "工程师绩效排名", path: "/engineer-performance/ranking", icon: "TrendingUp" },
        ],
      },
      {
        label: "审批与监控",
        items: [
          { name: "审批中心", path: "/approvals", icon: "ClipboardCheck" },
          { name: "预警中心", path: "/alerts", icon: "AlertTriangle" },
        ],
      },
      {
        label: "个人中心",
        items: [
          { name: "通知中心", path: "/notifications", icon: "Bell" },
          { name: "知识管理", path: "/knowledge-base", icon: "BookOpen" },
          { name: "个人设置", path: "/settings", icon: "Settings" },
        ],
      },
    ],
    sales_director: [
      {
        label: "团队管理",
        items: [
          {
            name: "销售总监工作台",
            path: "/sales-director-dashboard",
            icon: "LayoutDashboard",
          },
          { name: "销售团队管理", path: "/sales/team", icon: "Users" },
          { name: "销售目标", path: "/sales/targets", icon: "Target" },
        ],
      },
      {
        label: "销售监控",
        items: [
          { name: "销售统计", path: "/sales/statistics", icon: "BarChart3" },
          { name: "销售漏斗", path: "/sales/funnel", icon: "Target" },
          { name: "CPQ配置报价", path: "/sales/cpq", icon: "Calculator" },
          { name: "客户管理", path: "/customers", icon: "Building2" },
          { name: "商机看板", path: "/opportunities", icon: "Target" },
        ],
      },
      {
        label: "审批与监控",
        items: [
          { name: "审批中心", path: "/approvals", icon: "ClipboardCheck" },
          { name: "预警中心", path: "/alerts", icon: "AlertTriangle" },
          { name: "问题管理", path: "/issues", icon: "AlertCircle" },
        ],
      },
      {
        label: "项目跟踪",
        items: [
          { name: "项目看板", path: "/board", icon: "Kanban" },
          { name: "项目列表", path: "/projects", icon: "Briefcase" },
        ],
      },
      {
        label: "个人中心",
        items: [
          { name: "通知中心", path: "/notifications", icon: "Bell" },
          {
            name: "知识管理",
            path: "/knowledge-base",
            icon: "BookOpen",
          },
          { name: "个人设置", path: "/settings", icon: "Settings" },
        ],
      },
    ],
    sales_manager: [
      {
        label: "销售工作",
        items: [
          {
            name: "销售工作台",
            path: "/sales-dashboard",
            icon: "LayoutDashboard",
          },
          { name: "客户管理", path: "/sales/customers", icon: "Building2" },
          { name: "商机管理", path: "/sales/opportunities", icon: "Target" },
        ],
      },
      {
        label: "销售业务",
        items: [
          { name: "线索评估", path: "/lead-assessment", icon: "Target" },
          { name: "报价管理", path: "/sales/quotes", icon: "Calculator" },
          { name: "CPQ配置报价", path: "/sales/cpq", icon: "Calculator" },
          { name: "合同管理", path: "/sales/contracts", icon: "FileCheck" },
          { name: "回款跟踪", path: "/payments", icon: "CreditCard" },
          { name: "应收账款", path: "/sales/receivables", icon: "CreditCard" },
        ],
      },
      {
        label: "团队管理",
        items: [
          { name: "团队业绩", path: "/sales/team/performance", icon: "Users" },
          { name: "团队统计", path: "/sales/statistics", icon: "BarChart3" },
          { name: "销售目标", path: "/sales/targets", icon: "Target" },
        ],
      },
      {
        label: "项目跟踪",
        items: [
          { name: "项目进度", path: "/sales-projects", icon: "Briefcase" },
          { name: "项目看板", path: "/board", icon: "Kanban" },
          { name: "项目列表", path: "/projects", icon: "Briefcase" },
        ],
      },
      {
        label: "审批与监控",
        items: [
          { name: "审批中心", path: "/approvals", icon: "ClipboardCheck" },
          { name: "预警中心", path: "/alerts", icon: "AlertTriangle" },
        ],
      },
      {
        label: "个人中心",
        items: [
          { name: "通知中心", path: "/notifications", icon: "Bell" },
          {
            name: "知识管理",
            path: "/knowledge-base",
            icon: "BookOpen",
          },
          { name: "个人设置", path: "/settings", icon: "Settings" },
        ],
      },
    ],
    // 默认配置（用于未定义专门菜单的角色）
    default_user: [
      {
        label: "概览",
        items: [
          { name: "工作台", path: "/workstation", icon: "LayoutDashboard" },
          { name: "运营大屏", path: "/operation", icon: "BarChart3" },
        ],
      },
      {
        label: "项目管理",
        items: [
          { name: "项目看板", path: "/board", icon: "Kanban" },
          { name: "排期看板", path: "/schedule", icon: "Calendar" },
          { name: "任务中心", path: "/tasks", icon: "ListTodo" },
        ],
      },
      {
        label: "团队管理",
        items: [
          { name: "工程师绩效排名", path: "/engineer-performance/ranking", icon: "TrendingUp" },
          { name: "审批中心", path: "/approvals", icon: "ClipboardCheck" },
          { name: "预警中心", path: "/alerts", icon: "AlertTriangle" },
        ],
      },
      {
        label: "个人中心",
        items: [
          { name: "通知中心", path: "/notifications", icon: "Bell" },
          { name: "知识管理", path: "/knowledge-base", icon: "BookOpen" },
          { name: "个人设置", path: "/settings", icon: "Settings" },
        ],
      },
    ],
    hr_manager: [
      {
        label: "人力资源",
        items: [
          {
            name: "人事工作台",
            path: "/hr-dashboard",
            icon: "LayoutDashboard",
          },
          { name: "人员管理", path: "/employees", icon: "Users" },
          { name: "绩效管理", path: "/performance", icon: "Award" },
        ],
      },
      {
        label: "个人中心",
        items: [
          { name: "通知中心", path: "/notifications", icon: "Bell" },
          { name: "知识管理", path: "/knowledge-base", icon: "BookOpen" },
          { name: "个人设置", path: "/settings", icon: "Settings" },
        ],
      },
    ],
  };

  return navConfigs[role] || navConfigs.default_user;
}

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
 * 检查是否是工程师角色
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
