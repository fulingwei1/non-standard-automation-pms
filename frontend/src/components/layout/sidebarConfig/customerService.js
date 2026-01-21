/**
 * 客服相关导航组配置
 * 包括客服经理和客服工程师
 *
 * permission: 访问该菜单所需的权限码
 * permissionLabel: 无权限时显示的提示文字
 */

// Customer service manager nav groups
export const customerServiceManagerNavGroups = [
  {
    label: "客服管理",
    items: [
      {
        name: "工作台",
        path: "/dashboard",
        icon: "LayoutDashboard"
      },
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban", permission: "project:project:read", permissionLabel: "项目查看" },
      { name: "任务中心", path: "/progress-tracking/tasks", icon: "ListTodo", permission: "project:task:read", permissionLabel: "任务查看" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle", permission: "issue:manage", permissionLabel: "问题管理" }
    ]
  },
  {
    label: "监控与预警",
    items: [
      { name: "预警中心", path: "/alerts", icon: "AlertTriangle", permission: "alert:read", permissionLabel: "预警查看" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle", permission: "issue:read", permissionLabel: "问题查看" }
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
        path: "/dashboard",
        icon: "LayoutDashboard"
      },
      { name: "服务工单", path: "/service-tickets", icon: "FileText", permission: "service:ticket:read", permissionLabel: "服务工单" },
      {
        name: "服务记录",
        path: "/service-records",
        icon: "ClipboardCheck",
        permission: "service:record:read",
        permissionLabel: "服务记录"
      },
      {
        name: "客户沟通",
        path: "/customer-communications",
        icon: "MessageSquare",
        permission: "customer:communication:read",
        permissionLabel: "客户沟通"
      },
      {
        name: "满意度调查",
        path: "/customer-satisfaction",
        icon: "Star",
        permission: "customer:satisfaction:read",
        permissionLabel: "满意度调查"
      },
      { name: "服务分析", path: "/service-analytics", icon: "BarChart3", permission: "service:analytics:read", permissionLabel: "服务分析" },
      {
        name: "知识库",
        path: "/service-knowledge-base",
        icon: "BookOpen"
      },
      { name: "任务中心", path: "/progress-tracking/tasks", icon: "ListTodo", permission: "project:task:read", permissionLabel: "任务查看" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle", permission: "issue:read", permissionLabel: "问题查看" },
      { name: "工时填报", path: "/timesheet", icon: "Clock" }
    ]
  },
  {
    label: "监控与预警",
    items: [
      { name: "预警中心", path: "/alerts", icon: "AlertTriangle", permission: "alert:read", permissionLabel: "预警查看" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle", permission: "issue:read", permissionLabel: "问题查看" }
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
