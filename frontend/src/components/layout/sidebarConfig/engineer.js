/**
 * 工程师和团队负责人导航组配置
 *
 * permission: 访问该菜单所需的权限码
 * permissionLabel: 无权限时显示的提示文字
 */

// Engineer nav with workstation (Gantt/Calendar view)
export const engineerNavGroups = [
  {
    label: "我的工作",
    items: [
      { name: "工作台", path: "/workstation", icon: "LayoutDashboard" },
      { name: "任务中心", path: "/progress-tracking/tasks", icon: "ListTodo", permission: "project:task:read", permissionLabel: "任务查看" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle", permission: "issue:read", permissionLabel: "问题查看" },
      { name: "工时填报", path: "/timesheet", icon: "Clock" }
    ]
  },
  {
    label: "项目跟踪",
    items: [
      { name: "项目进度", path: "/sales-projects", icon: "Briefcase", permission: "project:project:read", permissionLabel: "项目查看" },
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban", permission: "project:project:read", permissionLabel: "项目查看" }
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
      { name: "我的绩效", path: "/personal/my-performance", icon: "Award", permission: "performance:self:read", permissionLabel: "个人绩效" },
      { name: "我的奖金", path: "/personal/my-bonus", icon: "DollarSign", permission: "bonus:self:read", permissionLabel: "个人奖金" },
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

// Team leader nav groups
export const teamLeaderNavGroups = [
  {
    label: "团队管理",
    items: [
      { name: "任务中心", path: "/progress-tracking/tasks", icon: "ListTodo", permission: "task:manage", permissionLabel: "任务管理" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle", permission: "issue:manage", permissionLabel: "问题管理" }
    ]
  },
  {
    label: "项目跟踪",
    items: [
      { name: "项目进度", path: "/sales-projects", icon: "Briefcase", permission: "project:project:read", permissionLabel: "项目查看" },
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban", permission: "project:project:read", permissionLabel: "项目查看" }
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
      { name: "工时填报", path: "/timesheet", icon: "Clock" },
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  }
];
