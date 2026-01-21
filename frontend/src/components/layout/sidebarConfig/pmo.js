/**
 * PMO相关导航组配置
 * 包括PMO总监和PMC（项目经理）
 *
 * permission: 访问该菜单所需的权限码
 * permissionLabel: 无权限时显示的提示文字
 */

// PMO Director nav groups (项目管理部总监)
export const pmoDirectorNavGroups = [
  {
    label: "概览",
    items: [
      { name: "工作台", path: "/dashboard", icon: "LayoutDashboard" },
      { name: "PMO 驾驶舱", path: "/pmo/dashboard", icon: "LayoutDashboard", permission: "pmo:dashboard:read", permissionLabel: "PMO驾驶舱" },
      { name: "运营大屏", path: "/operation", icon: "BarChart3", permission: "operation:dashboard:read", permissionLabel: "运营大屏" },
      { name: "工作中心", path: "/work-center", icon: "LayoutDashboard" },
      { name: "预警中心", path: "/alerts", icon: "AlertTriangle", badge: "3", permission: "alert:read", permissionLabel: "预警查看" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle", permission: "issue:read", permissionLabel: "问题查看" },
      { name: "通知中心", path: "/notifications", icon: "Bell", badge: "5" },
      { name: "审批中心", path: "/approvals", icon: "ClipboardCheck", badge: "2", permission: "approval:read", permissionLabel: "审批查看" },
      { name: "知识管理", path: "/knowledge-base", icon: "BookOpen" }
    ]
  },
  {
    label: "项目管理",
    items: [
      { name: "项目阶段视图", path: "/stage-view", icon: "Workflow", permission: "project:stage:read", permissionLabel: "项目阶段查看" },
      { name: "立项管理", path: "/pmo/initiations", icon: "FileText", permission: "project:initiation:read", permissionLabel: "立项管理" },
      { name: "风险预警", path: "/pmo/risk-wall", icon: "AlertTriangle", permission: "project:risk:read", permissionLabel: "风险预警" },
      { name: "项目结项", path: "/pmo/closure", icon: "CheckCircle2", permission: "project:close", permissionLabel: "项目结项" },
      { name: "项目复盘", path: "/projects/reviews", icon: "FileText", permission: "project_review:read", permissionLabel: "项目复盘" },
      { name: "最佳实践", path: "/projects/best-practices/recommend", icon: "Sparkles", permission: "project:bestpractice:read", permissionLabel: "最佳实践" },
      { name: "资源总览", path: "/pmo/resource-overview", icon: "Users", permission: "resource:read", permissionLabel: "资源查看" },
      { name: "项目周报", path: "/pmo/weekly-report", icon: "BarChart3", permission: "project:report:read", permissionLabel: "项目报表" }
    ]
  },
  {
    label: "进度跟踪",
    items: [
      { name: "任务中心", path: "/progress-tracking/tasks", icon: "ListTodo", permission: "project:task:read", permissionLabel: "任务查看" },
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban", permission: "project:project:read", permissionLabel: "项目查看" },
      { name: "排期看板", path: "/progress-tracking/schedule", icon: "Calendar", permission: "project:schedule:read", permissionLabel: "排期查看" },
      { name: "进度报告", path: "/progress-tracking/reports", icon: "FileText", permission: "project:progress:read", permissionLabel: "进度报告" },
      { name: "里程碑管理", path: "/progress-tracking/milestones", icon: "CheckCircle2", permission: "project:milestone:read", permissionLabel: "里程碑管理" },
      { name: "甘特图", path: "/progress-tracking/gantt", icon: "BarChart3", permission: "project:gantt:read", permissionLabel: "甘特图查看" }
    ]
  },
  {
    label: "团队管理",
    items: [
      { name: "工程师绩效排名", path: "/engineer-performance/ranking", icon: "TrendingUp", permission: "performance:read", permissionLabel: "绩效查看" },
      { name: "工时管理", path: "/timesheet", icon: "Clock", permission: "timesheet:manage", permissionLabel: "工时管理" }
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
      { name: "PMO 驾驶舱", path: "/pmo/dashboard", icon: "LayoutDashboard", permission: "pmo:dashboard:read", permissionLabel: "PMO驾驶舱" },
      { name: "运营大屏", path: "/operation", icon: "BarChart3", permission: "operation:dashboard:read", permissionLabel: "运营大屏" }
    ]
  },
  {
    label: "生产计划",
    items: [
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban", permission: "project:project:read", permissionLabel: "项目查看" },
      { name: "排期看板", path: "/progress-tracking/schedule", icon: "Calendar", permission: "project:schedule:read", permissionLabel: "排期查看" },
      { name: "齐套分析", path: "/material-analysis", icon: "Package", permission: "material:analysis:read", permissionLabel: "齐套分析" }
    ]
  },
  {
    label: "采购跟踪",
    items: [
      { name: "采购订单", path: "/purchases", icon: "ShoppingCart", permission: "purchase:read", permissionLabel: "采购订单查看" },
      { name: "缺料管理", path: "/shortage", icon: "Package", permission: "material:shortage:read", permissionLabel: "缺料管理" },
      { name: "齐套检查", path: "/kit-check", icon: "CheckCircle2", permission: "material:kit:read", permissionLabel: "齐套检查" },
      { name: "预警中心", path: "/alerts", icon: "AlertTriangle", badge: "3", permission: "alert:read", permissionLabel: "预警查看" }
    ]
  },
  {
    label: "发货管理",
    items: [
      { name: "发货计划", path: "/pmc/delivery-plan", icon: "Calendar", permission: "delivery:plan:read", permissionLabel: "发货计划" },
      { name: "发货订单", path: "/pmc/delivery-orders", icon: "Truck", permission: "delivery:order:read", permissionLabel: "发货订单" },
      {
        name: "待发货",
        path: "/pmc/delivery-orders?status=pending",
        icon: "Package",
        permission: "delivery:order:read",
        permissionLabel: "发货订单"
      },
      {
        name: "在途订单",
        path: "/pmc/delivery-orders?status=in_transit",
        icon: "Truck",
        permission: "delivery:order:read",
        permissionLabel: "发货订单"
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
