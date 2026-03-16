/**
 * 默认导航组配置
 * 用于管理员和通用场景
 *
 * permission: 访问该菜单所需的权限码
 * permissionAny: 命中任一权限即可访问
 * permissionLabel: 无权限时显示的提示文字
 */

export const defaultNavGroups = [
  // 1. 概览
  {
    label: "概览",
    items: [
      { name: "工作台", path: "/dashboard", icon: "LayoutDashboard", badge: null },
      { name: "运营大屏", path: "/operation", icon: "BarChart3", permission: "operation:dashboard:read", permissionLabel: "运营大屏" },
      { name: "通知中心", path: "/notifications", icon: "Bell", badge: "5" },
      { name: "审批中心", path: "/approvals", icon: "ClipboardCheck", badge: "2", permission: "approval:read", permissionLabel: "审批查看" },
      { name: "知识库", path: "/knowledge-base", icon: "BookOpen" }
    ]
  },
    {
    label: "战略管理",
    items: [
      { name: "决策驾驶舱", path: "/strategy/strategy-dashboard", icon: "Gauge", permission: "executive:dashboard:read", permissionLabel: "决策驾驶舱" },
      { name: "战略分析", path: "/strategy/analysis", icon: "Target", permission: "strategy:dashboard:read", permissionLabel: "战略分析" },
      { name: "战略地图", path: "/strategy/map", icon: "Map", permission: "strategy:dashboard:read", permissionLabel: "战略地图" },
      { name: "CSF 管理", path: "/strategy/csf", icon: "Layers", permission: "strategy:csf:read", permissionLabel: "CSF 管理" },
      { name: "KPI 管理", path: "/strategy/kpi", icon: "Activity", permission: "strategy:kpi:read", permissionLabel: "KPI 管理" },
      { name: "重点工作", path: "/strategy/annual-work", icon: "Briefcase", permission: "strategy:annual-work:read", permissionLabel: "重点工作" },
      { name: "战略分解", path: "/strategy/decomposition", icon: "GitBranch", permission: "strategy:decomposition:read", permissionLabel: "战略分解" },
      { name: "战略日历", path: "/strategy/calendar", icon: "Calendar", permission: "strategy:calendar:read", permissionLabel: "战略日历" },
      { name: "AI战略助手", path: "/strategy/ai-assistant", icon: "Sparkles", permission: "strategy:dashboard:read", permissionLabel: "AI战略助手" },
      { name: "同比分析", path: "/strategy/comparison", icon: "TrendingUp", permission: "strategy:comparison:read", permissionLabel: "同比分析" },
      { name: "关键决策", path: "/key-decisions", icon: "Lightbulb", permission: "executive:decision:read", permissionLabel: "关键决策" },
      { name: "管理节拍", path: "/management-rhythm-dashboard", icon: "Activity", permission: "pmo:rhythm:read", permissionLabel: "管理节拍" }
    ]
  },
  // 2. 销售管理
  {
    label: "销售管理",
    items: [
      // 工作站入口
      {
        name: "销售工作站",
        path: "/sales/workstation",
        icon: "Monitor",
        permissionAny: ["sales:opportunity:read", "sales:lead:read", "sales:funnel:read"],
        permissionLabel: "销售工作站"
      },
      // 战略层
      { name: "目标预测", path: "/sales/forecast-dashboard", icon: "BarChart3", permission: "sales:funnel:read", permissionLabel: "目标预测" },
      // 漏斗流程层 (L2C顺序)
      { name: "销售漏斗", path: "/sales/funnel", icon: "TrendingDown", permission: "sales:funnel:read", permissionLabel: "销售漏斗" },
      {
        name: "商机中心",
        path: "/sales/opportunity-center",
        icon: "Target",
        permissionAny: ["sales:lead:read", "sales:opportunity:read"],
        permissionLabel: "商机中心"
      },
      { name: "投标管理", path: "/bidding", icon: "Target", permission: "sales:bid:read", permissionLabel: "投标管理" },
      { name: "报价管理", path: "/cost-quotes/quotes", icon: "Calculator", permission: "sales:quote:read", permissionLabel: "报价管理" },
      { name: "合同管理", path: "/sales/contracts", icon: "FileCheck", permission: "sales:contract:read", permissionLabel: "合同管理" },
      { name: "立项管理", path: "/pmo/initiations", icon: "FileText", permission: "project:initiation:read", permissionLabel: "立项管理" },
      // 客户关系层
      { name: "客户管理", path: "/sales/customers", icon: "Building2", permission: "customer:read", permissionLabel: "客户查看" },
      { name: "对手分析", path: "/sales/competitor-analysis", icon: "BarChart3", permission: "sales:opportunity:read", permissionLabel: "对手分析" },
      // 财务回收层
      { name: "应收账款", path: "/sales/receivables", icon: "CreditCard", permission: "finance:receivable:read", permissionLabel: "应收账款" },
      { name: "发票管理", path: "/invoices", icon: "Receipt", permission: "finance:invoice:read", permissionLabel: "发票管理" },
      // 团队管理层
      {
        name: "销售团队",
        path: "/sales/team-center",
        icon: "Users",
        permissionAny: ["sales:team:read", "sales:opportunity:read"],
        permissionLabel: "销售团队"
      },
      { name: "数据质量", path: "/sales/data-quality", icon: "Star", permission: "sales:opportunity:read", permissionLabel: "数据质量" }
    ]
  },
  // 4. 售前技术
  {
    label: "售前技术",
    items: [
      // 工作台
      {
        name: "售前工作台",
        path: "/presales-workbench",
        icon: "Monitor",
        permissionAny: ["presales:task:read", "presales:task:manage"],
        permissionLabel: "售前工作台"
      },
      // 业务功能
      { name: "技术方案", path: "/presales/technical-solutions", icon: "Lightbulb", permission: "presales:task:read", permissionLabel: "技术方案" },
      { name: "成本估算", path: "/presales/cost-estimation", icon: "Calculator", permission: "presales:task:read", permissionLabel: "成本估算" },
      // 资源与工具
      { name: "模板库", path: "/presales/templates", icon: "Layers", permission: "presales:task:read", permissionLabel: "模板库" },
      // 运营管理
      { name: "数据分析", path: "/presales/presale-analytics", icon: "BarChart3", permission: "sales:funnel:read", permissionLabel: "售前数据分析" }
    ]
  },
  // 5. 项目管理
  {
    label: "项目管理",
    items: [
      // 概览
      { name: "项目驾驶舱", path: "/project/dashboard-center", icon: "Gauge", permission: "project:project:read", permissionLabel: "项目驾驶舱" },
      // 项目中心 - 整合项目列表、看板、流水线、里程碑等多视图
      { name: "项目中心", path: "/board", icon: "Kanban", permission: "project:project:read", permissionLabel: "项目中心" },
      // 规划层
      { name: "甘特与资源", path: "/gantt-resource", icon: "GitBranch", permission: "project:read", permissionLabel: "甘特与资源" },
      { name: "AI项目工具", path: "/ai-project-tools", icon: "Sparkles", permission: "project:project:read", permissionLabel: "AI项目工具" },
      // 执行层
      { name: "任务中心", path: "/tasks", icon: "ListTodo", permission: "project:project:read", permissionLabel: "任务中心" },
      // 监控层
      {
        name: "项目成本中心",
        path: "/project/cost-center",
        icon: "CreditCard",
        permissionAny: ["budget:read", "cost:accounting:read"],
        permissionLabel: "项目成本中心"
      },
      // 收尾层（整合结项、复盘、经验教训）
      { name: "项目收尾", path: "/project-closing", icon: "CheckCircle2", permission: "project:close", permissionLabel: "项目收尾" }
    ]
  },
  // 6. 工程技术
  {
    label: "工程技术",
    items: [
      {
        name: "ECN中心",
        path: "/change-management/ecn-center",
        icon: "FileText",
        permissionAny: ["ecn:read", "ecn:type:read", "ecn:statistics:read"],
        permissionLabel: "ECN中心"
      },
      { name: "技术评审", path: "/technical-reviews", icon: "FileCheck", permission: "technical:review:read", permissionLabel: "技术评审" }
    ]
  },
  // 7. 研发管理
  {
    label: "研发管理",
    items: [
      { name: "研发项目", path: "/rd-projects", icon: "Briefcase", permission: "rd:project:read", permissionLabel: "研发项目" },
      { name: "研发成本", path: "/rd-cost", icon: "DollarSign", permission: "rd:cost:read", permissionLabel: "研发成本" }
    ]
  },
  // 8. 采购管理
  {
    label: "采购管理",
    items: [
      {
        name: "采购执行中心",
        path: "/procurement/execution-center",
        icon: "ShoppingCart",
        permissionAny: ["purchase:read", "purchase:request:read", "purchase:receipt:read"],
        permissionLabel: "采购执行中心"
      },
      { name: "供应商管理", path: "/suppliers", icon: "Building2", permission: "supplier:read", permissionLabel: "供应商管理" },
      {
        name: "物料中心",
        path: "/procurement/material-center",
        icon: "Layers",
        permissionAny: ["bom:read", "material:read", "material:demand:read"],
        permissionLabel: "物料中心"
      },
      {
        name: "采购分析中心",
        path: "/procurement/analysis-center",
        icon: "BarChart3",
        permissionAny: ["material:analysis:read", "purchase:read", "purchase:analysis:read"],
        permissionLabel: "采购分析中心"
      }
    ]
  },
  // 9. 生产管理
  {
    label: "生产管理",
    items: [
      {
        name: "异常中心",
        path: "/production/exception-center",
        icon: "AlertCircle",
        permissionAny: ["issue:read", "production:exception:read"],
        permissionLabel: "异常中心"
      },
      { name: "生产看板", path: "/production-board", icon: "Kanban", permission: "production:board:read", permissionLabel: "生产看板" },
      { name: "产能分析", path: "/production/capacity-analysis", icon: "BarChart3", permission: "production:board:read", permissionLabel: "产能分析" },
      {
        name: "生产执行中心",
        path: "/production/execution-center",
        icon: "ClipboardList",
        permissionAny: ["workorder:read", "dispatch:read", "production:plan:read"],
        permissionLabel: "生产执行中心"
      },
      {
        name: "装配中心",
        path: "/production/assembly-center",
        icon: "Wrench",
        permissionAny: ["assembly:task:read", "production:board:read"],
        permissionLabel: "装配中心"
      },
      { name: "领料管理", path: "/material-requisitions", icon: "Package", permission: "material:requisition:read", permissionLabel: "领料管理" },
      {
        name: "现场资源",
        path: "/production/resource-center",
        icon: "Building2",
        permissionAny: ["workshop:read", "worker:read"],
        permissionLabel: "现场资源"
      },
      { name: "外协订单", path: "/outsourcing-orders", icon: "Truck", permission: "outsourcing:read", permissionLabel: "外协订单" },
      { name: "发货管理", path: "/pmc/delivery-orders", icon: "Truck", permission: "delivery:order:read", permissionLabel: "发货管理" }
    ]
  },
  // 10. 客服管理
  {
    label: "客服管理",
    items: [
      {
        name: "客服管理中心",
        path: "/customer-service/center",
        icon: "FileText",
        permissionAny: ["service:read", "acceptance:read", "installation_dispatch:read"],
        permissionLabel: "客服管理中心"
      }
    ]
  },
  // 11. 财务管理
  {
    label: "财务分析",
    items: [
      {
        name: "成本中心",
        path: "/finance/cost-center",
        icon: "Calculator",
        permission: "cost:accounting:read",
        permissionLabel: "成本中心"
      },
      { name: "付款审批", path: "/payment-approval", icon: "ClipboardCheck", permission: "payment:approve", permissionLabel: "付款审批" },
      { name: "项目结算", path: "/settlement", icon: "FileText", permission: "settlement:read", permissionLabel: "项目结算" },
      { name: "财务报表", path: "/financial-reports", icon: "BarChart3", permission: "finance:report:read", permissionLabel: "财务报表" },
      { name: "多币种", path: "/multi-currency", icon: "Coins", permission: "finance:read", permissionLabel: "多币种管理" }
    ],
    roles: ["finance", "accounting", "财务", "会计", "admin", "super_admin"]
  },
  // 12. 人力资源
  {
    label: "人力资源",
    items: [
      {
        name: "绩效中心",
        path: "/hr/performance-center",
        icon: "TrendingUp",
        permissionAny: ["performance:manage", "evaluation:config:manage"],
        permissionLabel: "绩效中心"
      },
      { name: "资质管理", path: "/qualifications", icon: "Award", permission: "qualification:read", permissionLabel: "资质管理" },
      {
        name: "人才匹配中心",
        path: "/hr/talent-matching-center",
        icon: "Layers",
        permissionAny: ["staff:tag:manage", "staff:profile:read", "staff:need:read", "staff:match:read"],
        permissionLabel: "人才匹配中心"
      }
    ]
  },
  // 13. 个人中心
  {
    label: "个人中心",
    items: [
      { name: "工时填报", path: "/timesheet", icon: "Clock" },
      { name: "我的绩效", path: "/personal/my-performance", icon: "TrendingUp" },
      { name: "绩效评价", path: "/evaluation-tasks", icon: "ListTodo", permission: "evaluation:task:read", permissionLabel: "绩效评价" },
      { name: "工程师绩效", path: "/engineer-performance", icon: "Gauge", permission: "performance:engineer:read", permissionLabel: "工程师绩效" },
      { name: "工程师协作", path: "/engineer-performance/collaboration", icon: "Users", permission: "engineer:collaboration:read", permissionLabel: "工程师协作" },
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  },
  // 14. 系统管理
  {
    label: "系统管理",
    items: [
      {
        name: "模板中心",
        path: "/system/template-center",
        icon: "Layers",
        permission: "system:template:manage",
        permissionLabel: "模板中心"
      },
      {
        name: "账号权限中心",
        path: "/system/account-permission-center",
        icon: "Users",
        permissionAny: ["USER_VIEW", "ROLE_VIEW"],
        permissionLabel: "账号权限中心"
      },
      {
        name: "组织架构中心",
        path: "/system/organization-center",
        icon: "Building2",
        permissionAny: ["system:org:manage", "system:position:manage"],
        permissionLabel: "组织架构中心"
      },
      { name: "定时任务", path: "/scheduler-monitoring", icon: "Activity", permission: "system:scheduler:read", permissionLabel: "定时任务" },
      { name: "审计日志", path: "/audit-logs", icon: "FileText", permission: "AUDIT_VIEW", permissionLabel: "审计日志" },
      { name: "数据导入导出", path: "/data-import-export", icon: "Archive", permission: "system:data:manage", permissionLabel: "数据导入导出" }
    ],
    roles: ["admin", "super_admin"]
  }
];
