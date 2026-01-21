/**
 * 生产相关导航组配置
 * 统一菜单结构，通过权限控制功能开放
 *
 * permission: 访问该菜单所需的权限码
 * permissionLabel: 无权限时显示的提示文字
 */

// 统一的生产角色导航组（生产经理、装配工、制造总监共用）
export const productionNavGroups = [
  {
    label: "生产管理",
    items: [
      { name: "工作台", path: "/dashboard", icon: "LayoutDashboard" },
      { name: "运营大屏", path: "/operation", icon: "BarChart3", permission: "operation:dashboard:read", permissionLabel: "运营大屏" },
      { name: "工作中心", path: "/work-center", icon: "LayoutDashboard" },
      { name: "生产看板", path: "/production-board", icon: "Kanban", permission: "production:board:read", permissionLabel: "生产看板" },
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban", permission: "project:project:read", permissionLabel: "项目查看" },
      { name: "排期看板", path: "/progress-tracking/schedule", icon: "Calendar", permission: "project:schedule:read", permissionLabel: "排期查看" },
      { name: "装配任务", path: "/assembly-tasks", icon: "Wrench", permission: "assembly:task:read", permissionLabel: "装配任务" },
      { name: "装配齐套", path: "/assembly-kit", icon: "Wrench", permission: "assembly:kit:read", permissionLabel: "装配齐套" },
      { name: "齐套检查", path: "/kit-check", icon: "CheckCircle2", permission: "material:kit:read", permissionLabel: "齐套检查" },
      { name: "齐套分析", path: "/material-analysis", icon: "Package", permission: "material:analysis:read", permissionLabel: "齐套分析" },
      { name: "项目进度", path: "/sales-projects", icon: "Briefcase", permission: "project:project:read", permissionLabel: "项目查看" },
      { name: "工程师绩效排名", path: "/engineer-performance/ranking", icon: "TrendingUp", permission: "performance:read", permissionLabel: "绩效查看" }
    ]
  },
  {
    label: "监控与预警",
    items: [
      { name: "预警中心", path: "/alerts", icon: "AlertTriangle", badge: "3", permission: "alert:read", permissionLabel: "预警查看" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle", permission: "issue:read", permissionLabel: "问题查看" }
    ]
  },
  {
    label: "个人中心",
    items: [
      { name: "通知中心", path: "/notifications", icon: "Bell" },
      { name: "工时填报", path: "/timesheet", icon: "Clock" },
      { name: "企业文化墙", path: "/culture-wall", icon: "Heart" },
      { name: "知识管理", path: "/knowledge-base", icon: "BookOpen" },
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  }
];

// 为了向后兼容，保留原有导出名称，都指向统一配置
export const productionManagerNavGroups = productionNavGroups;
export const assemblerNavGroups = productionNavGroups;
export const manufacturingDirectorNavGroups = productionNavGroups;
