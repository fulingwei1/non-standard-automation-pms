/**
 * 采购相关导航组配置
 * 包括采购员、采购工程师、采购经理
 *
 * permission: 访问该菜单所需的权限码
 * permissionLabel: 无权限时显示的提示文字
 */

// Buyer nav groups
export const buyerNavGroups = [
  {
    label: "概览",
    items: [
      {
        name: "工作台",
        path: "/dashboard",
        icon: "LayoutDashboard"
      }
    ]
  },
  {
    label: "采购管理",
    items: [
      { name: "采购订单", path: "/purchases", icon: "ShoppingCart", permission: "purchase:read", permissionLabel: "采购订单查看" },
      {
        name: "物料成本",
        path: "/cost-quotes/material-costs",
        icon: "DollarSign",
        permission: "cost:material:read",
        permissionLabel: "物料成本查看"
      },
      { name: "供应商管理", path: "/suppliers", icon: "Building2", permission: "supplier:read", permissionLabel: "供应商查看" },
      { name: "缺料管理", path: "/shortage", icon: "Package", permission: "material:shortage:read", permissionLabel: "缺料管理" },
      { name: "收货管理", path: "/purchases/receipts", icon: "Truck", permission: "purchase:receipt:read", permissionLabel: "收货管理" }
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
      { name: "工时填报", path: "/timesheet", icon: "Clock" },
      { name: "知识管理", path: "/knowledge-base", icon: "BookOpen" },
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
        name: "工作台",
        path: "/dashboard",
        icon: "LayoutDashboard"
      },
      { name: "采购订单", path: "/purchases", icon: "ShoppingCart", permission: "purchase:read", permissionLabel: "采购订单查看" },
      { name: "采购申请", path: "/purchase-requests", icon: "FileText", permission: "purchase:request:read", permissionLabel: "采购申请查看" },
      { name: "从BOM生成订单", path: "/purchases/from-bom", icon: "Package", permission: "purchase:create", permissionLabel: "采购订单创建" },
      { name: "供应商管理", path: "/suppliers", icon: "Building2", permission: "supplier:read", permissionLabel: "供应商查看" }
    ]
  },
  {
    label: "物料管理",
    items: [
      { name: "物料跟踪", path: "/materials", icon: "Package", permission: "material:read", permissionLabel: "物料查看" },
      { name: "收货管理", path: "/purchases/receipts", icon: "Truck", permission: "purchase:receipt:read", permissionLabel: "收货管理" },
      { name: "齐套分析", path: "/material-analysis", icon: "Boxes", permission: "material:analysis:read", permissionLabel: "齐套分析" },
      { name: "BOM装配配置", path: "/bom-assembly-attrs", icon: "Settings", permission: "bom:config:manage", permissionLabel: "BOM配置管理" }
    ]
  },
  {
    label: "成本控制",
    items: [
      {
        name: "物料成本",
        path: "/cost-quotes/material-costs",
        icon: "DollarSign",
        permission: "cost:material:read",
        permissionLabel: "物料成本查看"
      },
      { name: "预算管理", path: "/budgets", icon: "CreditCard", permission: "budget:read", permissionLabel: "预算查看" },
      { name: "成本分析", path: "/cost-analysis", icon: "BarChart3", permission: "cost:analysis:read", permissionLabel: "成本分析" }
    ]
  },
  {
    label: "监控与预警",
    items: [
      { name: "预警中心", path: "/alerts", icon: "AlertTriangle", permission: "alert:read", permissionLabel: "预警查看" }
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
        name: "工作台",
        path: "/dashboard",
        icon: "LayoutDashboard"
      }
    ]
  },
  {
    label: "项目管理",
    items: [
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban", permission: "project:project:read", permissionLabel: "项目查看" },
      { name: "排期看板", path: "/progress-tracking/schedule", icon: "Calendar", permission: "project:schedule:read", permissionLabel: "排期查看" }
    ]
  },
  {
    label: "采购管理",
    items: [
      { name: "采购订单", path: "/purchases", icon: "ShoppingCart", permission: "purchase:read", permissionLabel: "采购订单查看" },
      { name: "供应商管理", path: "/suppliers", icon: "Building2", permission: "supplier:manage", permissionLabel: "供应商管理" },
      { name: "缺料管理", path: "/shortage", icon: "Package", permission: "material:shortage:read", permissionLabel: "缺料管理" },
      { name: "收货管理", path: "/purchases/receipts", icon: "Truck", permission: "purchase:receipt:read", permissionLabel: "收货管理" },
      { name: "齐套分析", path: "/material-analysis", icon: "Package", permission: "material:analysis:read", permissionLabel: "齐套分析" }
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
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  }
];
