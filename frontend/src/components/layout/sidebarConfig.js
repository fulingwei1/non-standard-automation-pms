/**
 * Sidebar导航配置
 * 包含所有角色的导航组配置
 */

// Default navigation groups (for admin and general use)
export const defaultNavGroups = [
  {
    label: "概览",
    items: [
      {
        name: "管理员工作台",
        path: "/admin-dashboard",
        icon: "LayoutDashboard"
      },
      { name: "运营大屏", path: "/operation", icon: "BarChart3" },
      {
        name: "工作中心",
        path: "/work-center",
        icon: "LayoutDashboard",
        badge: null
      },
      { name: "预警中心", path: "/alerts", icon: "AlertTriangle", badge: "3" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle" },
      { name: "通知中心", path: "/notifications", icon: "Bell", badge: "5" },
      {
        name: "审批中心",
        path: "/approvals",
        icon: "ClipboardCheck",
        badge: "2"
      },
      { name: "知识管理", path: "/knowledge-base", icon: "BookOpen" }
    ]
  },
  {
    label: "项目管理",
    items: [
      { name: "PMO 驾驶舱", path: "/pmo/dashboard", icon: "LayoutDashboard" },
      { name: "立项管理", path: "/pmo/initiations", icon: "FileText" },
      { name: "风险预警", path: "/pmo/risk-wall", icon: "AlertTriangle" },
      { name: "项目结项", path: "/pmo/closure", icon: "CheckCircle2" },
      { name: "项目复盘", path: "/projects/reviews", icon: "FileText" },
      {
        name: "最佳实践",
        path: "/projects/best-practices/recommend",
        icon: "Sparkles"
      },
      { name: "资源总览", path: "/pmo/resource-overview", icon: "Users" },
      { name: "项目周报", path: "/pmo/weekly-report", icon: "BarChart3" }
    ]
  },
  {
    label: "进度跟踪",
    items: [
      { name: "任务中心", path: "/progress-tracking/tasks", icon: "ListTodo" },
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban" },
      { name: "排期看板", path: "/progress-tracking/schedule", icon: "Calendar" },
      { name: "进度报告", path: "/progress-tracking/reports", icon: "FileText" },
      { name: "里程碑管理", path: "/progress-tracking/milestones", icon: "CheckCircle2" },
      { name: "WBS管理", path: "/progress-tracking/wbs", icon: "Layers" },
      { name: "甘特图", path: "/progress-tracking/gantt", icon: "BarChart3" }
    ]
  },
  {
    label: "采购管理",
    items: [
      { name: "采购订单", path: "/purchases", icon: "ShoppingCart" },
      { name: "缺料管理", path: "/shortage", icon: "Package" },
      { name: "齐套管理", path: "/material-readiness", icon: "Package" }
    ]
  },
  {
    label: "成本报价管理",
    items: [
      { name: "报价管理", path: "/cost-quotes/quotes", icon: "Calculator" },
      { name: "报价成本", path: "/cost-quotes/quote-costs", icon: "DollarSign" },
      { name: "物料成本", path: "/cost-quotes/material-costs", icon: "DollarSign" },
      { name: "财务成本", path: "/cost-quotes/financial-costs", icon: "DollarSign" },
      { name: "成本分析", path: "/cost-quotes/cost-analysis", icon: "BarChart3" },
      { name: "模板与CPQ", path: "/cost-quotes/templates", icon: "Layers" }
    ]
  },
  {
    label: "质量验收",
    items: [
      { name: "验收管理", path: "/acceptance", icon: "ClipboardList" },
      {
        name: "安装调试",
        path: "/installation-dispatch",
        icon: "Settings"
      }
    ]
  },
  {
    label: "变更管理",
    items: [
      { name: "ECN管理", path: "/change-management/ecn", icon: "FileText" },
      { name: "ECN类型", path: "/change-management/ecn-types", icon: "Layers" },
      { name: "逾期预警", path: "/change-management/ecn/overdue-alerts", icon: "AlertTriangle" },
      { name: "ECN统计", path: "/change-management/ecn/statistics", icon: "BarChart3" }
    ]
  },
  {
    label: "AI人员匹配",
    items: [
      { name: "标签字典", path: "/staff-matching/tags", icon: "Target" },
      { name: "员工档案", path: "/staff-matching/profiles", icon: "Users" },
      {
        name: "人员需求",
        path: "/staff-matching/staffing-needs",
        icon: "ClipboardList"
      },
      { name: "智能匹配", path: "/staff-matching/matching", icon: "Sparkles" }
    ]
  },
  {
    label: "人员管理",
    items: [
      { name: "工程师绩效排名", path: "/engineer-performance/ranking", icon: "TrendingUp" }
    ]
  },
  {
    label: "财务管理",
    items: [
      // 财务成本已迁移到"成本报价管理"模块
    ],
    roles: ["finance", "accounting", "财务", "会计", "admin", "super_admin"] // 财务部可见
  },
  {
    label: "个人中心",
    items: [
      { name: "工时填报", path: "/timesheet", icon: "Clock" },
      { name: "工作日志", path: "/work-log", icon: "ClipboardList" },
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  },
  {
    label: "系统管理",
    items: [
      { name: "用户管理", path: "/user-management", icon: "Users" },
      { name: "角色管理", path: "/role-management", icon: "Shield" },
      { name: "权限管理", path: "/permission-management", icon: "Key" },
      { name: "项目角色", path: "/project-role-types", icon: "UserCog" },
      { name: "问题模板", path: "/issue-templates", icon: "FileText" },
      { name: "调度器监控", path: "/scheduler-monitoring", icon: "Activity" },
      { name: "定时配置", path: "/scheduler-config", icon: "Cog" },
      { name: "客户管理", path: "/customer-management", icon: "Building2" },
      { name: "供应商管理", path: "/supplier-management-data", icon: "Truck" },
      { name: "部门管理", path: "/department-management", icon: "Building2" }
    ],
    roles: ["admin", "super_admin"] // 仅管理员可见
  }
];

// Engineer nav with workstation (Gantt/Calendar view)
export const engineerNavGroups = [
  {
    label: "我的工作",
    items: [
      { name: "工作台", path: "/workstation", icon: "LayoutDashboard" },
      { name: "任务中心", path: "/progress-tracking/tasks", icon: "ListTodo" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle" },
      { name: "工时填报", path: "/timesheet", icon: "Clock" }
    ]
  },
  {
    label: "项目跟踪",
    items: [
      { name: "项目进度", path: "/sales-projects", icon: "Briefcase" },
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban" }
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
      { name: "我的绩效", path: "/personal/my-performance", icon: "Award" },
      { name: "我的奖金", path: "/personal/my-bonus", icon: "DollarSign" },
      { name: "月度总结", path: "/personal/monthly-summary", icon: "FileText" },
      { name: "工作日志", path: "/work-log", icon: "ClipboardList" },
      {
        name: "知识管理",
        path: "/knowledge-base",
        icon: "BookOpen"
      },
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  }
];

// PMO Director nav groups (项目管理部总监)
export const pmoDirectorNavGroups = [
  {
    label: "概览",
    items: [
      { name: "PMO 驾驶舱", path: "/pmo/dashboard", icon: "LayoutDashboard" },
      { name: "运营大屏", path: "/operation", icon: "BarChart3" },
      { name: "工作中心", path: "/work-center", icon: "LayoutDashboard" },
      { name: "预警中心", path: "/alerts", icon: "AlertTriangle", badge: "3" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle" },
      { name: "通知中心", path: "/notifications", icon: "Bell", badge: "5" },
      { name: "审批中心", path: "/approvals", icon: "ClipboardCheck", badge: "2" },
      { name: "知识管理", path: "/knowledge-base", icon: "BookOpen" }
    ]
  },
  {
    label: "项目管理",
    items: [
      { name: "立项管理", path: "/pmo/initiations", icon: "FileText" },
      { name: "风险预警", path: "/pmo/risk-wall", icon: "AlertTriangle" },
      { name: "项目结项", path: "/pmo/closure", icon: "CheckCircle2" },
      { name: "项目复盘", path: "/projects/reviews", icon: "FileText" },
      { name: "最佳实践", path: "/projects/best-practices/recommend", icon: "Sparkles" },
      { name: "资源总览", path: "/pmo/resource-overview", icon: "Users" },
      { name: "项目周报", path: "/pmo/weekly-report", icon: "BarChart3" }
    ]
  },
  {
    label: "进度跟踪",
    items: [
      { name: "任务中心", path: "/progress-tracking/tasks", icon: "ListTodo" },
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban" },
      { name: "排期看板", path: "/progress-tracking/schedule", icon: "Calendar" },
      { name: "进度报告", path: "/progress-tracking/reports", icon: "FileText" },
      { name: "里程碑管理", path: "/progress-tracking/milestones", icon: "CheckCircle2" },
      { name: "甘特图", path: "/progress-tracking/gantt", icon: "BarChart3" }
    ]
  },
  {
    label: "团队管理",
    items: [
      { name: "工程师绩效排名", path: "/engineer-performance/ranking", icon: "TrendingUp" },
      { name: "工时管理", path: "/timesheet", icon: "Clock" }
    ]
  },
  {
    label: "个人中心",
    items: [
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  }
];

// PMC nav groups
export const pmcNavGroups = [
  {
    label: "概览",
    items: [
      { name: "PMO 驾驶舱", path: "/pmo/dashboard", icon: "LayoutDashboard" },
      { name: "运营大屏", path: "/operation", icon: "BarChart3" }
    ]
  },
  {
    label: "生产计划",
    items: [
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban" },
      { name: "排期看板", path: "/progress-tracking/schedule", icon: "Calendar" },
      { name: "齐套分析", path: "/material-analysis", icon: "Package" }
    ]
  },
  {
    label: "采购跟踪",
    items: [
      { name: "采购订单", path: "/purchases", icon: "ShoppingCart" },
      { name: "缺料管理", path: "/shortage", icon: "Package" },
      { name: "齐套检查", path: "/kit-check", icon: "CheckCircle2" },
      { name: "预警中心", path: "/alerts", icon: "AlertTriangle", badge: "3" }
    ]
  },
  {
    label: "发货管理",
    items: [
      { name: "发货计划", path: "/pmc/delivery-plan", icon: "Calendar" },
      { name: "发货订单", path: "/pmc/delivery-orders", icon: "Truck" },
      {
        name: "待发货",
        path: "/pmc/delivery-orders?status=pending",
        icon: "Package"
      },
      {
        name: "在途订单",
        path: "/pmc/delivery-orders?status=in_transit",
        icon: "Truck"
      }
    ]
  },
  {
    label: "个人中心",
    items: [
      {
        name: "工作中心",
        path: "/work-center",
        icon: "LayoutDashboard",
        badge: null
      },
      { name: "通知中心", path: "/notifications", icon: "Bell" },
      { name: "工时填报", path: "/timesheet", icon: "Clock" },
      { name: "工作日志", path: "/work-log", icon: "ClipboardList" },
      {
        name: "知识管理",
        path: "/knowledge-base",
        icon: "BookOpen"
      },
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  }
];

// Buyer nav groups
export const buyerNavGroups = [
  {
    label: "概览",
    items: [
      {
        name: "采购工作台",
        path: "/procurement-dashboard",
        icon: "LayoutDashboard"
      }
    ]
  },
  {
    label: "采购管理",
    items: [
      { name: "采购订单", path: "/purchases", icon: "ShoppingCart" },
      {
        name: "物料成本",
        path: "/cost-quotes/material-costs",
        icon: "DollarSign"
      },
      { name: "供应商管理", path: "/suppliers", icon: "Building2" },
      { name: "缺料管理", path: "/shortage", icon: "Package" },
      { name: "到货跟踪", path: "/arrivals", icon: "Truck" }
    ]
  },
  {
    label: "监控与预警",
    items: [{ name: "预警中心", path: "/alerts", icon: "AlertTriangle" }]
  },
  {
    label: "个人中心",
    items: [
      {
        name: "工作中心",
        path: "/work-center",
        icon: "LayoutDashboard",
        badge: null
      },
      { name: "通知中心", path: "/notifications", icon: "Bell" },
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

// Production manager nav groups
export const productionManagerNavGroups = [
  {
    label: "生产管理",
    items: [
      {
        name: "生产工作台",
        path: "/production-dashboard",
        icon: "LayoutDashboard"
      },
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban" },
      { name: "排期看板", path: "/progress-tracking/schedule", icon: "Calendar" }
    ]
  },
  {
    label: "采购管理",
    items: [
      { name: "采购订单", path: "/purchases", icon: "ShoppingCart" },
      { name: "缺料管理", path: "/shortage", icon: "Package" },
      { name: "齐套检查", path: "/kit-check", icon: "CheckCircle2" },
      { name: "齐套分析", path: "/material-analysis", icon: "Package" },
      { name: "装配齐套", path: "/assembly-kit", icon: "Wrench" },
      { name: "预警中心", path: "/alerts", icon: "AlertTriangle", badge: "3" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle" }
    ]
  },
  {
    label: "个人中心",
    items: [
      {
        name: "工作中心",
        path: "/work-center",
        icon: "LayoutDashboard",
        badge: null
      },
      { name: "通知中心", path: "/notifications", icon: "Bell" },
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

// Assembler specific nav groups
export const assemblerNavGroups = [
  {
    label: "我的工作",
    items: [
      { name: "装配任务", path: "/assembly-tasks", icon: "Wrench" },
      { name: "工时填报", path: "/timesheet", icon: "Clock" }
    ]
  },
  {
    label: "项目跟踪",
    items: [
      { name: "项目进度", path: "/sales-projects", icon: "Briefcase" },
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban" }
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
      {
        name: "工作中心",
        path: "/work-center",
        icon: "LayoutDashboard",
        badge: null
      },
      { name: "通知中心", path: "/notifications", icon: "Bell", badge: "5" },
      {
        name: "知识管理",
        path: "/knowledge-base",
        icon: "BookOpen"
      },
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  }
];

// Sales engineer nav groups
export const salesNavGroups = [
  {
    label: "销售工作",
    items: [
      { name: "销售工作台", path: "/sales-dashboard", icon: "LayoutDashboard" },
      { name: "客户管理", path: "/customers", icon: "Building2" },
      { name: "商机看板", path: "/opportunities", icon: "Target" }
    ]
  },
  {
    label: "销售管理",
    items: [
      { name: "线索评估", path: "/lead-assessment", icon: "Target" },
      { name: "报价管理", path: "/cost-quotes/quotes", icon: "Calculator" },
      { name: "合同管理", path: "/sales/contracts", icon: "FileCheck" },
      { name: "模板与CPQ", path: "/cost-quotes/templates", icon: "Layers" },
      { name: "技术评审", path: "/technical-reviews", icon: "FileCheck" },
      { name: "应收账款", path: "/sales/receivables", icon: "CreditCard" },
      { name: "回款跟踪", path: "/payments", icon: "CreditCard" },
      { name: "未中标分析", path: "/sales/loss-analysis", icon: "TrendingDown" },
      { name: "售前费用", path: "/sales/presale-expenses", icon: "DollarSign" },
      { name: "优先级管理", path: "/sales/priority", icon: "Star" },
      { name: "断链分析", path: "/sales/pipeline-break-analysis", icon: "AlertTriangle" },
      { name: "归责分析", path: "/sales/accountability-analysis", icon: "Users" },
      { name: "健康度监控", path: "/sales/health-monitoring", icon: "Activity" },
      { name: "延期分析", path: "/sales/delay-analysis", icon: "Clock" },
      { name: "成本超支分析", path: "/sales/cost-overrun-analysis", icon: "DollarSign" },
      { name: "信息质量分析", path: "/sales/information-gap-analysis", icon: "FileText" }
    ]
  },
  {
    label: "项目跟踪",
    items: [
      { name: "项目进度", path: "/sales-projects", icon: "Briefcase" },
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban" }
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

// Procurement engineer nav groups
export const procurementNavGroups = [
  {
    label: "采购工作",
    items: [
      {
        name: "采购工作台",
        path: "/procurement-dashboard",
        icon: "LayoutDashboard"
      },
      { name: "采购订单", path: "/purchases", icon: "ShoppingCart" },
      { name: "采购申请", path: "/purchase-requests", icon: "FileText" },
      { name: "从BOM生成订单", path: "/purchases/from-bom", icon: "Package" },
      { name: "供应商管理", path: "/suppliers", icon: "Building2" }
    ]
  },
  {
    label: "物料管理",
    items: [
      { name: "物料跟踪", path: "/materials", icon: "Package" },
      { name: "收货管理", path: "/purchases/receipts", icon: "Truck" },
      { name: "到货跟踪", path: "/arrivals", icon: "Truck" },
      { name: "齐套分析", path: "/material-analysis", icon: "Boxes" },
      { name: "BOM装配配置", path: "/bom-assembly-attrs", icon: "Settings" }
    ]
  },
  {
    label: "成本控制",
    items: [
      {
        name: "物料成本",
        path: "/cost-quotes/material-costs",
        icon: "DollarSign"
      },
      { name: "预算管理", path: "/budgets", icon: "CreditCard" },
      { name: "成本分析", path: "/cost-analysis", icon: "BarChart3" }
    ]
  },
  {
    label: "监控与预警",
    items: [
      { name: "预警中心", path: "/alerts", icon: "AlertTriangle" },
      { name: "缺料预警", path: "/shortage-alert", icon: "AlertTriangle" }
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

// Procurement manager nav groups
export const procurementManagerNavGroups = [
  {
    label: "概览",
    items: [
      {
        name: "采购经理工作台",
        path: "/procurement-manager-dashboard",
        icon: "LayoutDashboard"
      }
    ]
  },
  {
    label: "项目管理",
    items: [
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban" },
      { name: "排期看板", path: "/progress-tracking/schedule", icon: "Calendar" }
    ]
  },
  {
    label: "采购管理",
    items: [
      { name: "采购订单", path: "/purchases", icon: "ShoppingCart" },
      { name: "供应商管理", path: "/suppliers", icon: "Building2" },
      { name: "缺料管理", path: "/shortage", icon: "Package" },
      { name: "到货跟踪", path: "/arrivals", icon: "Truck" },
      { name: "齐套分析", path: "/material-analysis", icon: "Package" }
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
      { name: "通知中心", path: "/notifications", icon: "Bell" },
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  }
];

// Finance manager nav groups (内联定义，需要导出)
export const financeManagerNavGroups = [
  {
    label: "财务管理",
    items: [
      {
        name: "财务工作台",
        path: "/finance-manager-dashboard",
        icon: "LayoutDashboard"
      },
      {
        name: "财务成本",
        path: "/cost-quotes/financial-costs",
        icon: "DollarSign"
      },
      { name: "成本核算", path: "/costs", icon: "Calculator" },
      {
        name: "付款审批",
        path: "/payment-approval",
        icon: "ClipboardCheck"
      },
      { name: "项目结算", path: "/settlement", icon: "FileText" },
      { name: "财务报表", path: "/financial-reports", icon: "BarChart3" },
      { name: "决策驾驶舱", path: "/executive-dashboard", icon: "Gauge" }
    ]
  },
  {
    label: "监控与预警",
    items: [{ name: "预警中心", path: "/alerts", icon: "AlertTriangle" }]
  },
  {
    label: "个人中心",
    items: [
      { name: "通知中心", path: "/notifications", icon: "Bell" },
      {
        name: "知识管理",
        path: "/knowledge-base",
        icon: "BookOpen"
      },
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  }
];

// Manufacturing director nav groups
export const manufacturingDirectorNavGroups = [
  {
    label: "概览",
    items: [
      {
        name: "制造总监工作台",
        path: "/manufacturing-director-dashboard",
        icon: "LayoutDashboard"
      },
      { name: "运营大屏", path: "/operation", icon: "BarChart3" }
    ]
  },
  {
    label: "生产管理",
    items: [
      {
        name: "生产看板",
        path: "/production-dashboard",
        icon: "LayoutDashboard"
      },
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban" },
      { name: "排期看板", path: "/progress-tracking/schedule", icon: "Calendar" }
    ]
  },
  {
    label: "采购管理",
    items: [
      { name: "采购订单", path: "/purchases", icon: "ShoppingCart" },
      { name: "齐套分析", path: "/material-analysis", icon: "Package" },
      {
        name: "预警中心",
        path: "/alerts",
        icon: "AlertTriangle",
        badge: "3"
      },
      { name: "问题管理", path: "/issues", icon: "AlertCircle" }
    ]
  },
  {
    label: "人员管理",
    items: [
      { name: "工程师绩效排名", path: "/engineer-performance/ranking", icon: "TrendingUp" }
    ]
  },
  {
    label: "个人中心",
    items: [
      { name: "通知中心", path: "/notifications", icon: "Bell" },
      { name: "企业文化墙", path: "/culture-wall", icon: "Heart" },
      {
        name: "知识管理",
        path: "/knowledge-base",
        icon: "BookOpen"
      },
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  }
];

// Customer service manager nav groups
export const customerServiceManagerNavGroups = [
  {
    label: "客服管理",
    items: [
      {
        name: "客服工作台",
        path: "/customer-service-dashboard",
        icon: "LayoutDashboard"
      },
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban" },
      { name: "任务中心", path: "/progress-tracking/tasks", icon: "ListTodo" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle" }
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
      { name: "通知中心", path: "/notifications", icon: "Bell" },
      {
        name: "知识管理",
        path: "/knowledge-base",
        icon: "BookOpen"
      },
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  }
];

// Customer service engineer nav groups
export const customerServiceEngineerNavGroups = [
  {
    label: "我的工作",
    items: [
      {
        name: "工作台",
        path: "/customer-service-dashboard",
        icon: "LayoutDashboard"
      },
      { name: "服务工单", path: "/service-tickets", icon: "FileText" },
      {
        name: "服务记录",
        path: "/service-records",
        icon: "ClipboardCheck"
      },
      {
        name: "客户沟通",
        path: "/customer-communications",
        icon: "MessageSquare"
      },
      {
        name: "满意度调查",
        path: "/customer-satisfaction",
        icon: "Star"
      },
      { name: "服务分析", path: "/service-analytics", icon: "BarChart3" },
      {
        name: "知识库",
        path: "/service-knowledge-base",
        icon: "BookOpen"
      },
      { name: "任务中心", path: "/progress-tracking/tasks", icon: "ListTodo" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle" },
      { name: "工时填报", path: "/timesheet", icon: "Clock" }
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
      { name: "通知中心", path: "/notifications", icon: "Bell" },
      {
        name: "知识管理",
        path: "/knowledge-base",
        icon: "BookOpen"
      },
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  }
];

// Team leader nav groups
export const teamLeaderNavGroups = [
  {
    label: "团队管理",
    items: [
      { name: "任务中心", path: "/progress-tracking/tasks", icon: "ListTodo" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle" }
    ]
  },
  {
    label: "项目跟踪",
    items: [
      { name: "项目进度", path: "/sales-projects", icon: "Briefcase" },
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban" }
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
      { name: "通知中心", path: "/notifications", icon: "Bell" },
      { name: "工时填报", path: "/timesheet", icon: "Clock" },
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
