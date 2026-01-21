/**
 * 财务经理导航组配置
 *
 * permission: 访问该菜单所需的权限码
 * permissionLabel: 无权限时显示的提示文字
 */

// Finance manager nav groups
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
        icon: "DollarSign",
        permission: "finance:cost:read",
        permissionLabel: "财务成本查看"
      },
      { name: "成本核算", path: "/costs", icon: "Calculator", permission: "cost:accounting:read", permissionLabel: "成本核算" },
      {
        name: "付款审批",
        path: "/payment-approval",
        icon: "ClipboardCheck",
        permission: "payment:approve",
        permissionLabel: "付款审批"
      },
      { name: "项目结算", path: "/settlement", icon: "FileText", permission: "settlement:read", permissionLabel: "项目结算" },
      { name: "财务报表", path: "/financial-reports", icon: "BarChart3", permission: "finance:report:read", permissionLabel: "财务报表" },
      { name: "决策驾驶舱", path: "/executive-dashboard", icon: "Gauge", permission: "executive:dashboard:read", permissionLabel: "决策驾驶舱" }
    ]
  },
  {
    label: "监控与预警",
    items: [{ name: "预警中心", path: "/alerts", icon: "AlertTriangle", permission: "alert:read", permissionLabel: "预警查看" }]
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
