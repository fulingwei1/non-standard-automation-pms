/**
 * 销售相关导航组配置
 * 包括销售工程师、商务支持、售前技术工程师
 *
 * permission: 访问该菜单所需的权限码
 * permissionLabel: 无权限时显示的提示文字
 */

// Sales engineer nav groups
export const salesNavGroups = [
  {
    label: "销售工作",
    items: [
      { name: "销售工作台", path: "/sales-dashboard", icon: "LayoutDashboard" },
      { name: "客户管理", path: "/customers", icon: "Building2", permission: "customer:read", permissionLabel: "客户查看" },
      { name: "商机看板", path: "/opportunities", icon: "Target", permission: "sales:opportunity:read", permissionLabel: "商机查看" },
      { name: "线索管理", path: "/sales/leads", icon: "Users", permission: "sales:lead:read", permissionLabel: "线索查看" },
      { name: "报价管理", path: "/cost-quotes/quotes", icon: "Calculator", permission: "sales:quote:read", permissionLabel: "报价查看" },
      { name: "合同管理", path: "/sales/contracts", icon: "FileCheck", permission: "sales:contract:read", permissionLabel: "合同查看" },
      { name: "模板与CPQ", path: "/cost-quotes/templates", icon: "Layers", permission: "sales:quote:read", permissionLabel: "报价模板" },
      { name: "技术评审", path: "/technical-reviews", icon: "FileCheck", permission: "sales:technical:read", permissionLabel: "技术评审" },
      { name: "应收账款", path: "/sales/receivables", icon: "CreditCard", permission: "finance:receivable:read", permissionLabel: "应收账款" },
      { name: "回款跟踪", path: "/payments", icon: "CreditCard", permission: "finance:payment:read", permissionLabel: "回款查看" },
      { name: "未中标分析", path: "/sales/loss-analysis", icon: "TrendingDown", permission: "sales:analysis:read", permissionLabel: "销售分析" },
      { name: "售前费用", path: "/sales/presale-expenses", icon: "DollarSign", permission: "sales:expense:read", permissionLabel: "费用查看" },
      { name: "优先级管理", path: "/sales/priority", icon: "Star", permission: "sales:lead:update", permissionLabel: "线索管理" },
      { name: "断链分析", path: "/sales/pipeline-break-analysis", icon: "AlertTriangle", permission: "sales:analysis:read", permissionLabel: "销售分析" },
      { name: "归责分析", path: "/sales/accountability-analysis", icon: "Users", permission: "sales:analysis:read", permissionLabel: "销售分析" },
      { name: "健康度监控", path: "/sales/health-monitoring", icon: "Activity", permission: "sales:analysis:read", permissionLabel: "销售分析" },
      { name: "延期分析", path: "/sales/delay-analysis", icon: "Clock", permission: "sales:analysis:read", permissionLabel: "销售分析" },
      { name: "成本超支分析", path: "/sales/cost-overrun-analysis", icon: "DollarSign", permission: "sales:analysis:read", permissionLabel: "销售分析" },
      { name: "信息质量���析", path: "/sales/information-gap-analysis", icon: "FileText", permission: "sales:analysis:read", permissionLabel: "销售分析" }
    ]
  },
  {
    label: "项目管理",
    items: [
      { name: "项目进度", path: "/sales-projects", icon: "Briefcase", permission: "project:project:read", permissionLabel: "项目查看" },
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban", permission: "project:project:read", permissionLabel: "项目查看" },
      { name: "项目阶段视图", path: "/stage-view", icon: "Workflow", permission: "project:project:read", permissionLabel: "项目查看" },
      { name: "项目列表", path: "/projects", icon: "List", permission: "project:project:read", permissionLabel: "项目查看" },
      { name: "项目结项", path: "/pmo/closure", icon: "CheckCircle2", permission: "project:close", permissionLabel: "项目结项" },
      { name: "项目复盘", path: "/projects/reviews", icon: "FileText", permission: "project_review:read", permissionLabel: "项目复盘" },
      { name: "最佳实践", path: "/projects/best-practices/recommend", icon: "Sparkles", permission: "project:project:read", permissionLabel: "项目查看" },
      { name: "项目周报", path: "/pmo/weekly-report", icon: "BarChart3", permission: "project:report:read", permissionLabel: "项目报表" }
    ]
  },
  {
    label: "监控与预警",
    items: [
      { name: "预警中心", path: "/alerts", icon: "AlertTriangle" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle" }
    ]
  },
  {
    label: "个人中心",
    items: [
      { name: "通知中心", path: "/notifications", icon: "Bell", badge: "3" },
      { name: "工时填报", path: "/timesheet", icon: "Clock" },
      {
        name: "知识管理",
        path: "/knowledge-base",
        icon: "BookOpen"
      },
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  }
];

// Business support nav groups
export const businessSupportNavGroups = [
  {
    label: "商务工作",
    items: [
      {
        name: "商务工作台",
        path: "/business-support",
        icon: "LayoutDashboard"
      },
      { name: "客户管理", path: "/customers", icon: "Building2" },
      { name: "投标管理", path: "/bidding", icon: "Target" }
    ]
  },
  {
    label: "合同与订单",
    items: [
      { name: "合同管理", path: "/contracts", icon: "FileCheck" },
      { name: "报价管理", path: "/quotations", icon: "Calculator" },
      { name: "项目订单", path: "/sales-projects", icon: "Briefcase" }
    ]
  },
  {
    label: "财务与发货",
    items: [
      { name: "回款跟踪", path: "/payments", icon: "CreditCard" },
      { name: "对账开票", path: "/invoices", icon: "Receipt" },
      { name: "出货管理", path: "/shipments", icon: "Package" }
    ]
  },
  {
    label: "文档与归档",
    items: [
      { name: "文件管理", path: "/documents", icon: "Archive" },
      { name: "验收管理", path: "/acceptance", icon: "ClipboardList" }
    ]
  },
  {
    label: "监控与预警",
    items: [
      { name: "预警中心", path: "/alerts", icon: "AlertTriangle" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle" }
    ]
  },
  {
    label: "个人中心",
    items: [
      { name: "通知中心", path: "/notifications", icon: "Bell", badge: "3" },
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  }
];

// Pre-sales technical engineer nav groups
export const presalesNavGroups = [
  {
    label: "技术支持",
    items: [
      { name: "工作台", path: "/presales-dashboard", icon: "LayoutDashboard" },
      { name: "任务中心", path: "/presales-tasks", icon: "ListTodo" }
    ]
  },
  {
    label: "方案管理",
    items: [
      { name: "方案中心", path: "/solutions", icon: "FileText" },
      { name: "需求调研", path: "/requirement-survey", icon: "ClipboardList" },
      { name: "技术评审", path: "/technical-reviews", icon: "FileCheck" },
      { name: "投标中心", path: "/bidding", icon: "Target" },
      { name: "未中标分析", path: "/sales/loss-analysis", icon: "TrendingDown" },
      { name: "售前费用", path: "/sales/presale-expenses", icon: "DollarSign" },
      { name: "断链分析", path: "/sales/pipeline-break-analysis", icon: "AlertTriangle" },
      { name: "归责分析", path: "/sales/accountability-analysis", icon: "Users" },
      { name: "健康度监控", path: "/sales/health-monitoring", icon: "Activity" },
      { name: "延期分析", path: "/sales/delay-analysis", icon: "Clock" },
      { name: "成本超支分析", path: "/sales/cost-overrun-analysis", icon: "DollarSign" },
      { name: "信息质量分析", path: "/sales/information-gap-analysis", icon: "FileText" }
    ]
  },
  {
    label: "知识库",
    items: [{ name: "知识检索", path: "/knowledge-base", icon: "BookOpen" }]
  },
  {
    label: "监控与预警",
    items: [
      { name: "预警中心", path: "/alerts", icon: "AlertTriangle" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle" }
    ]
  },
  {
    label: "个人中心",
    items: [
      { name: "通知中心", path: "/notifications", icon: "Bell", badge: "2" },
      { name: "工时填报", path: "/timesheet", icon: "Clock" },
      {
        name: "知识管理",
        path: "/knowledge-base",
        icon: "BookOpen"
      },
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  }
];
