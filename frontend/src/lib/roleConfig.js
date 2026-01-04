/**
 * 角色配置 - 定义每个角色的界面和功能权限
 */

// 角色定义
export const ROLE_DEFINITIONS = {
  chairman: {
    name: '董事长',
    dataScope: 'all',
    description: '公司战略决策、重大事项审批、全面监控',
    navGroups: ['overview', 'project', 'operation', 'quality', 'personal'],
  },
  gm: {
    name: '总经理',
    dataScope: 'all',
    description: '战略决策、重大项目审批、经营指标监控',
    navGroups: ['overview', 'project', 'operation', 'quality', 'personal'],
  },
  super_admin: {
    name: '管理员',
    dataScope: 'all',
    description: '系统配置、用户管理、权限分配、系统维护',
    navGroups: ['overview', 'project', 'operation', 'quality', 'system', 'personal'],
  },
  admin: {
    name: '系统管理员',
    dataScope: 'all',
    description: '系统配置、用户管理、权限分配',
    navGroups: ['overview', 'project', 'operation', 'quality', 'system', 'personal'],
  },
  dept_manager: {
    name: '部门经理',
    dataScope: 'department',
    description: '部门资源调配、人员绩效、项目协调',
    navGroups: ['overview', 'project', 'operation', 'quality', 'personal'],
  },
  pm: {
    name: '项目经理',
    dataScope: 'project',
    description: '项目全生命周期管理、进度把控、客户对接',
    navGroups: ['overview', 'project', 'operation', 'quality', 'personal'],
  },
  te: {
    name: '技术负责人',
    dataScope: 'project',
    description: '技术方案、设计评审、技术问题解决',
    navGroups: ['overview', 'project', 'quality', 'personal'],
  },
  me_leader: {
    name: '机械组长',
    dataScope: 'group',
    description: '机械设计任务分配、图纸审核',
    navGroups: ['overview', 'project', 'personal'],
    focusStages: ['S2', 'S3'],
  },
  ee_leader: {
    name: '电气组长',
    dataScope: 'group',
    description: '电气设计任务分配、程序审核',
    navGroups: ['overview', 'project', 'personal'],
    focusStages: ['S2', 'S4'],
  },
  te_leader: {
    name: '测试组长',
    dataScope: 'group',
    description: '测试方案、调试任务分配',
    navGroups: ['overview', 'project', 'personal'],
    focusStages: ['S6', 'S7'],
  },
  me_engineer: {
    name: '机械工程师',
    dataScope: 'self',
    description: '机械结构设计、出图',
    navGroups: ['engineer_work', 'personal'],
    focusStages: ['S3'],
  },
  ee_engineer: {
    name: '电气工程师',
    dataScope: 'self',
    description: '电气设计、PLC编程、接线',
    navGroups: ['engineer_work', 'personal'],
    focusStages: ['S4'],
  },
  sw_engineer: {
    name: '软件工程师',
    dataScope: 'self',
    description: '上位机软件、视觉算法开发',
    navGroups: ['engineer_work', 'personal'],
    focusStages: ['S4', 'S6'],
  },
  te_engineer: {
    name: '测试工程师',
    dataScope: 'self',
    description: '设备调试、测试验证',
    navGroups: ['engineer_work', 'personal'],
    focusStages: ['S6', 'S7'],
  },
  buyer: {
    name: '采购员',
    dataScope: 'procurement',
    description: '物料采购、供应商管理、到货跟踪',
    navGroups: ['overview', 'procurement', 'personal'],
    focusStages: ['S5'],
  },
  warehouse: {
    name: '仓库管理员',
    dataScope: 'warehouse',
    description: '物料入库、出库、库存管理',
    navGroups: ['warehouse', 'personal'],
    focusStages: ['S5'],
  },
  assembler: {
    name: '装配技工',
    dataScope: 'self',
    description: '设备组装、机械调整、缺料反馈、质量反馈',
    navGroups: ['assembler_work', 'personal'],
    focusStages: ['S6'],
  },
  qa: {
    name: '品质工程师',
    dataScope: 'all',
    description: '过程质量、出货检验、问题追溯',
    navGroups: ['overview', 'quality', 'personal'],
    focusStages: ['S5', 'S6', 'S7'],
  },
  pmc: {
    name: 'PMC计划员',
    dataScope: 'all',
    description: '生产计划、物料计划、产能协调',
    navGroups: ['overview', 'project', 'operation', 'personal'],
    focusStages: ['S5', 'S6'],
  },
  sales: {
    name: '销售工程师',
    dataScope: 'customer',
    description: '客户需求对接、合同签订、回款跟踪',
    navGroups: ['sales_work', 'sales', 'personal'],
    focusStages: ['S1', 'S7'],
  },
  presales: {
    name: '售前技术工程师',
    dataScope: 'customer',
    description: '技术方案设计、客户需求对接、投标技术支持',
    navGroups: ['presales_work', 'presales_mgmt', 'knowledge', 'personal'],
    focusStages: ['S1', 'S2'],
  },
  business_support: {
    name: '商务支持专员',
    dataScope: 'customer',
    description: '客户建档、合同管理、投标支持、对账开票、回款跟踪、文档归档',
    navGroups: ['business_support'],
    focusStages: ['S1', 'S7', 'S8'],
  },
  finance: {
    name: '财务人员',
    dataScope: 'finance',
    description: '成本核算、付款审批、项目结算',
    navGroups: ['overview', 'finance', 'personal'],
  },
  finance_manager: {
    name: '财务经理',
    dataScope: 'finance',
    description: '财务团队管理、预算控制、财务分析、资金管理',
    navGroups: ['overview', 'finance', 'personal'],
  },
  hr_manager: {
    name: '人事经理',
    dataScope: 'all',
    description: '人力资源规划、招聘管理、绩效管理、员工关系',
    navGroups: ['overview', 'personal'],
  },
  viewer: {
    name: '只读用户',
    dataScope: 'limited',
    description: '仅查看报表和进度',
    navGroups: ['overview'],
  },
  // 销售/支持角色
  sales_director: {
    name: '销售总监',
    dataScope: 'all',
    description: '销售战略规划、团队管理、业绩监控',
    navGroups: ['overview', 'project', 'personal'],
    focusStages: ['S1', 'S7'],
  },
  sales_manager: {
    name: '销售经理',
    dataScope: 'department',
    description: '销售团队管理、客户关系维护、业绩达成',
    navGroups: ['sales_work', 'sales', 'personal'],
    focusStages: ['S1', 'S7'],
  },
  presales_manager: {
    name: '售前技术部经理',
    dataScope: 'department',
    description: '售前团队管理、技术方案审核、投标支持',
    navGroups: ['presales_work', 'presales_mgmt', 'personal'],
    focusStages: ['S1', 'S2'],
  },
  // 项目管理角色
  project_dept_manager: {
    name: '项目部经理',
    dataScope: 'department',
    description: '项目团队管理、资源协调、进度监控',
    navGroups: ['overview', 'project', 'operation', 'quality', 'personal'],
    focusStages: ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7'],
  },
  // 工程技术中心角色
  tech_dev_manager: {
    name: '技术开发部经理',
    dataScope: 'department',
    description: '技术团队管理、研发规划、技术评审',
    navGroups: ['overview', 'project', 'quality', 'personal'],
    focusStages: ['S2', 'S3', 'S4'],
  },
  rd_engineer: {
    name: '研发工程师',
    dataScope: 'self',
    description: '技术研发、创新设计、技术验证',
    navGroups: ['engineer_work', 'personal'],
    focusStages: ['S2', 'S3', 'S4'],
  },
  me_dept_manager: {
    name: '机械部经理',
    dataScope: 'department',
    description: '机械团队管理、设计审核、资源分配',
    navGroups: ['overview', 'project', 'personal'],
    focusStages: ['S2', 'S3'],
  },
  te_dept_manager: {
    name: '测试部经理',
    dataScope: 'department',
    description: '测试团队管理、测试方案审核、质量把控',
    navGroups: ['overview', 'project', 'quality', 'personal'],
    focusStages: ['S6', 'S7'],
  },
  ee_dept_manager: {
    name: '电气部经理',
    dataScope: 'department',
    description: '电气团队管理、设计审核、程序审核',
    navGroups: ['overview', 'project', 'personal'],
    focusStages: ['S2', 'S4'],
  },
  // 采购部角色
  procurement_manager: {
    name: '采购部经理',
    dataScope: 'department',
    description: '采购团队管理、供应商管理、采购审批',
    navGroups: ['overview', 'procurement', 'personal'],
    focusStages: ['S5'],
  },
  procurement_engineer: {
    name: '采购工程师',
    dataScope: 'procurement',
    description: '物料采购、供应商对接、到货跟踪',
    navGroups: ['overview', 'procurement', 'personal'],
    focusStages: ['S5'],
  },
  // 制造中心角色
  manufacturing_director: {
    name: '制造总监',
    dataScope: 'all',
    description: '制造中心全面管理、生产计划审批、资源协调',
    navGroups: ['overview', 'project', 'operation', 'quality', 'personal'],
    focusStages: ['S4', 'S5', 'S6', 'S7'],
  },
  production_manager: {
    name: '生产部经理',
    dataScope: 'department',
    description: '生产计划管理、车间调度、人员管理、异常处理',
    navGroups: ['overview', 'project', 'operation', 'personal'],
    focusStages: ['S5', 'S6'],
  },
  assembler_mechanic: {
    name: '装配钳工',
    dataScope: 'self',
    description: '机械装配、钳工加工、缺料反馈、质量反馈',
    navGroups: ['assembler_work', 'personal'],
    focusStages: ['S6'],
  },
  assembler_electrician: {
    name: '装配电工',
    dataScope: 'self',
    description: '电气装配、接线调试、缺料反馈、质量反馈',
    navGroups: ['assembler_work', 'personal'],
    focusStages: ['S6'],
  },
  customer_service_manager: {
    name: '客服部经理',
    dataScope: 'department',
    description: '客服团队管理、客户问题协调、服务质量监控',
    navGroups: ['overview', 'project', 'personal'],
    focusStages: ['S8', 'S9'],
  },
  customer_service_engineer: {
    name: '客服工程师',
    dataScope: 'customer',
    description: '客户技术支持、问题处理、现场服务、客户沟通',
    navGroups: ['overview', 'project', 'personal'],
    focusStages: ['S8', 'S9'],
  },
}

// 导航组定义
export const NAV_GROUPS = {
  overview: {
    label: '概览',
    items: [
      { name: '仪表盘', path: '/', icon: 'LayoutDashboard' },
      { name: '运营大屏', path: '/operation', icon: 'BarChart3' },
    ],
  },
  project: {
    label: '项目管理',
    items: [
      { name: '项目看板', path: '/board', icon: 'Kanban' },
      { name: '项目列表', path: '/projects', icon: 'Briefcase' },
      { name: '排期看板', path: '/schedule', icon: 'Calendar' },
    ],
  },
  tasks: {
    label: '我的工作',
    items: [
      { name: '任务中心', path: '/tasks', icon: 'ListTodo' },
      { name: '工时填报', path: '/timesheet', icon: 'Clock' },
    ],
  },
  // 工程师专用导航（含甘特图工作台）
  engineer_work: {
    label: '我的工作',
    items: [
      { name: '工作台', path: '/workstation', icon: 'LayoutDashboard' },
      { name: '任务中心', path: '/tasks', icon: 'ListTodo' },
      { name: '工时填报', path: '/timesheet', icon: 'Clock' },
    ],
  },
  // 装配技工专用导航
  assembler_work: {
    label: '我的工作',
    items: [
      { name: '装配任务', path: '/assembly-tasks', icon: 'Wrench' },
      { name: '工时填报', path: '/timesheet', icon: 'Clock' },
    ],
  },
  operation: {
    label: '运营管理',
    items: [
      { name: '采购订单', path: '/purchases', icon: 'ShoppingCart' },
      { name: '齐套分析', path: '/materials', icon: 'Package' },
      { name: '预警中心', path: '/alerts', icon: 'AlertTriangle', badge: '3' },
      { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
    ],
  },
  procurement: {
    label: '采购管理',
    items: [
      { name: '采购订单', path: '/purchases', icon: 'ShoppingCart' },
      { name: '供应商管理', path: '/suppliers', icon: 'Building2' },
      { name: '到货跟踪', path: '/arrivals', icon: 'Truck' },
    ],
  },
  warehouse: {
    label: '仓库管理',
    items: [
      { name: '入库管理', path: '/inbound', icon: 'PackagePlus' },
      { name: '出库管理', path: '/outbound', icon: 'PackageMinus' },
      { name: '库存查询', path: '/inventory', icon: 'Boxes' },
    ],
  },
  quality: {
    label: '质量验收',
    items: [
      { name: '验收管理', path: '/acceptance', icon: 'ClipboardList' },
      { name: '审批中心', path: '/approvals', icon: 'ClipboardCheck', badge: '2' },
    ],
  },
  // 销售专用工作台导航
  sales_work: {
    label: '我的工作',
    items: [
      { name: '工作台', path: '/sales-dashboard', icon: 'LayoutDashboard' },
      { name: '客户管理', path: '/customers', icon: 'Users' },
      { name: '商机跟踪', path: '/opportunities', icon: 'Target' },
    ],
  },
  sales: {
    label: '销售管理',
    items: [
      { name: '线索评估', path: '/lead-assessment', icon: 'Target' },
      { name: '报价管理', path: '/quotations', icon: 'FileText' },
      { name: '合同管理', path: '/contracts', icon: 'FileSignature' },
      { name: '回款管理', path: '/payments', icon: 'CreditCard' },
      { name: '项目跟踪', path: '/sales-projects', icon: 'FolderKanban' },
    ],
  },
  // 商务支持专员专用导航
  business_support: {
    label: '商务工作',
    items: [
      { name: '商务工作台', path: '/business-support', icon: 'LayoutDashboard' },
      { name: '客户管理', path: '/customers', icon: 'Building2' },
      { name: '投标管理', path: '/bidding', icon: 'Target' },
      { name: '合同管理', path: '/contracts', icon: 'FileCheck' },
      { name: '报价管理', path: '/quotations', icon: 'Calculator' },
      { name: '项目订单', path: '/sales-projects', icon: 'Briefcase' },
      { name: '回款跟踪', path: '/payments', icon: 'CreditCard' },
      { name: '对账开票', path: '/invoices', icon: 'Receipt' },
      { name: '验收管理', path: '/acceptance', icon: 'ClipboardList' },
    ],
  },
  // 售前技术工程师专用导航
  presales_work: {
    label: '技术支持',
    items: [
      { name: '工作台', path: '/presales-dashboard', icon: 'LayoutDashboard' },
      { name: '任务中心', path: '/presales-tasks', icon: 'ListTodo' },
    ],
  },
  presales_mgmt: {
    label: '方案管理',
    items: [
      { name: '方案中心', path: '/solutions', icon: 'FileText' },
      { name: '需求调研', path: '/requirement-survey', icon: 'ClipboardList' },
      { name: '投标中心', path: '/bidding', icon: 'Target' },
    ],
  },
  knowledge: {
    label: '知识库',
    items: [
      { name: '知识检索', path: '/knowledge-base', icon: 'BookOpen' },
    ],
  },
  finance: {
    label: '财务管理',
    items: [
      { name: '成本核算', path: '/costs', icon: 'Calculator' },
      { name: '付款审批', path: '/payment-approval', icon: 'FileCheck' },
      { name: '项目结算', path: '/settlement', icon: 'Receipt' },
    ],
  },
  system: {
    label: '系统管理',
    items: [
      { name: '用户管理', path: '/users', icon: 'UserCog' },
      { name: '角色权限', path: '/roles', icon: 'Shield' },
      { name: '系统配置', path: '/config', icon: 'Cog' },
    ],
  },
  personal: {
    label: '个人中心',
    items: [
      { name: '通知中心', path: '/notifications', icon: 'Bell', badge: '5' },
      { name: '工时填报', path: '/timesheet', icon: 'Clock' },
      { name: '个人设置', path: '/settings', icon: 'Settings' },
    ],
  },
}

// 获取角色的导航配置
export function getNavForRole(roleCode) {
  const role = ROLE_DEFINITIONS[roleCode]
  if (!role) return []
  
  return role.navGroups
    .map(groupKey => NAV_GROUPS[groupKey])
    .filter(Boolean)
}

// 获取角色信息
export function getRoleInfo(roleCode) {
  return ROLE_DEFINITIONS[roleCode] || ROLE_DEFINITIONS.viewer
}

// 获取角色关注的阶段
export function getRoleFocusStages(roleCode) {
  const role = ROLE_DEFINITIONS[roleCode]
  return role?.focusStages || []
}

// 判断角色是否有管理权限
export function hasManagePermission(roleCode) {
  const manageRoles = ['admin', 'gm', 'dept_manager', 'pm', 'te']
  return manageRoles.includes(roleCode)
}

// 判断角色是否为工程师级别（只能看自己的任务）
export function isEngineerRole(roleCode) {
  const engineerRoles = ['me_engineer', 'ee_engineer', 'sw_engineer', 'te_engineer', 'assembler']
  return engineerRoles.includes(roleCode)
}

// 模拟用户数据
export const DEMO_USERS = {
  admin: {
    id: 1,
    username: 'admin',
    name: '系统管理员',
    role: 'admin',
    department: '信息中心',
    avatar: null,
  },
  dept_manager: {
    id: 5,
    username: 'zhang_manager',
    name: '张经理',
    role: 'dept_manager',
    department: '生产部',
    avatar: null,
  },
  pm: {
    id: 6,
    username: 'li_pm',
    name: '李项目经理',
    role: 'pm',
    department: '项目部',
    avatar: null,
  },
  te_leader: {
    id: 4,
    username: 'wang_leader',
    name: '王组长',
    role: 'te_leader',
    department: '测试组',
    avatar: null,
  },
  assembler_mechanic: {
    id: 5,
    username: 'zhao_worker',
    name: '赵师傅',
    role: 'assembler_mechanic',
    department: '装配车间',
    avatar: null,
  },
  assembler_electrician: {
    id: 19,
    username: 'qian_electrician',
    name: '钱电工',
    role: 'assembler_electrician',
    department: '装配车间',
    avatar: null,
  },
  buyer: {
    id: 6,
    username: 'chen_buyer',
    name: '陈采购',
    role: 'buyer',
    department: '采购部',
    avatar: null,
  },
  pmc: {
    id: 7,
    username: 'liu_pmc',
    name: '刘计划员',
    role: 'pmc',
    department: 'PMC',
    avatar: null,
  },
  me_engineer: {
    id: 8,
    username: 'zhang_me',
    name: '张工',
    role: 'me_engineer',
    department: '机械组',
    avatar: null,
  },
  ee_engineer: {
    id: 9,
    username: 'sun_ee',
    name: '孙工',
    role: 'ee_engineer',
    department: '电气组',
    avatar: null,
  },
  sw_engineer: {
    id: 10,
    username: 'qian_sw',
    name: '钱工',
    role: 'sw_engineer',
    department: '软件组',
    avatar: null,
  },
  te_engineer: {
    id: 11,
    username: 'zhou_te',
    name: '周工',
    role: 'te_engineer',
    department: '测试组',
    avatar: null,
  },
  sales: {
    id: 12,
    username: 'zhang_sales',
    name: '张销售',
    role: 'sales',
    department: '销售部',
    avatar: null,
  },
  presales: {
    id: 13,
    username: 'li_presales',
    name: '李工',
    role: 'presales',
    department: '售前部',
    avatar: null,
  },
  business_support: {
    id: 14,
    username: 'wang_business',
    name: '王商务',
    role: 'business_support',
    department: '销售部',
    avatar: null,
  },
  // 销售/支持角色
  sales_director: {
    id: 20,
    username: 'liu_sales_director',
    name: '刘总监',
    role: 'sales_director',
    department: '销售部',
    avatar: null,
  },
  sales_manager: {
    id: 21,
    username: 'zhang_sales_mgr',
    name: '张经理',
    role: 'sales_manager',
    department: '销售部',
    avatar: null,
  },
  presales_manager: {
    id: 22,
    username: 'wang_presales_mgr',
    name: '王经理',
    role: 'presales_manager',
    department: '售前技术部',
    avatar: null,
  },
  // 项目管理角色
  project_dept_manager: {
    id: 23,
    username: 'sun_project_mgr',
    name: '孙经理',
    role: 'project_dept_manager',
    department: '项目部',
    avatar: null,
  },
  // 工程技术中心角色
  tech_dev_manager: {
    id: 24,
    username: 'zhou_tech_mgr',
    name: '周经理',
    role: 'tech_dev_manager',
    department: '技术开发部',
    avatar: null,
  },
  rd_engineer: {
    id: 25,
    username: 'wu_rd',
    name: '吴工',
    role: 'rd_engineer',
    department: '技术开发部',
    avatar: null,
  },
  me_dept_manager: {
    id: 26,
    username: 'zheng_me_mgr',
    name: '郑经理',
    role: 'me_dept_manager',
    department: '机械部',
    avatar: null,
  },
  te_dept_manager: {
    id: 27,
    username: 'wang_te_mgr',
    name: '王经理',
    role: 'te_dept_manager',
    department: '测试部',
    avatar: null,
  },
  ee_dept_manager: {
    id: 28,
    username: 'feng_ee_mgr',
    name: '冯经理',
    role: 'ee_dept_manager',
    department: '电气部',
    avatar: null,
  },
  // 采购部角色
  procurement_manager: {
    id: 29,
    username: 'chen_procurement_mgr',
    name: '陈经理',
    role: 'procurement_manager',
    department: '采购部',
    avatar: null,
  },
  procurement_engineer: {
    id: 30,
    username: 'chu_procurement',
    name: '褚工',
    role: 'procurement_engineer',
    department: '采购部',
    avatar: null,
  },
  // 制造中心角色
  manufacturing_director: {
    id: 15,
    username: 'liu_director',
    name: '刘总监',
    role: 'manufacturing_director',
    department: '制造中心',
    avatar: null,
  },
  production_manager: {
    id: 16,
    username: 'zhao_production',
    name: '赵经理',
    role: 'production_manager',
    department: '生产部',
    avatar: null,
  },
  customer_service_manager: {
    id: 17,
    username: 'sun_service_mgr',
    name: '孙经理',
    role: 'customer_service_manager',
    department: '客服部',
    avatar: null,
  },
  customer_service_engineer: {
    id: 18,
    username: 'qian_service',
    name: '钱工',
    role: 'customer_service_engineer',
    department: '客服部',
    avatar: null,
  },
  // 后台支持角色
  finance_manager: {
    id: 31,
    username: 'sun_finance_mgr',
    name: '孙经理',
    role: 'finance_manager',
    department: '财务部',
    avatar: null,
  },
  hr_manager: {
    id: 32,
    username: 'li_hr_mgr',
    name: '李经理',
    role: 'hr_manager',
    department: '人事部',
    avatar: null,
  },
}

