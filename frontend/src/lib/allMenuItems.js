/**
 * 系统完整菜单配置
 * 管理员可从此配置中选择菜单分配给不同角色
 */

// 所有可用菜单分组
export const allMenuGroups = [
  {
    id: "overview",
    label: "概览",
    items: [
      {
        id: "admin-dashboard",
        name: "管理员工作台",
        path: "/admin-dashboard",
        icon: "LayoutDashboard",
      },
      {
        id: "gm-dashboard",
        name: "总经理工作台",
        path: "/gm-dashboard",
        icon: "LayoutDashboard",
      },
      {
        id: "chairman-dashboard",
        name: "董事长工作台",
        path: "/chairman-dashboard",
        icon: "LayoutDashboard",
      },
      {
        id: "workstation",
        name: "工作台",
        path: "/workstation",
        icon: "LayoutDashboard",
      },
      {
        id: "operation",
        name: "运营大屏",
        path: "/operation",
        icon: "BarChart3",
      },
      {
        id: "business-reports",
        name: "经营报表",
        path: "/business-reports",
        icon: "BarChart3",
      },
      {
        id: "strategy-analysis",
        name: "战略分析",
        path: "/strategy-analysis",
        icon: "Target",
      },
    ],
  },
  {
    id: "project",
    label: "项目管理",
    items: [
      { id: "board", name: "项目看板", path: "/board", icon: "Kanban" },
      {
        id: "projects",
        name: "项目列表",
        path: "/projects",
        icon: "Briefcase",
      },
      { id: "schedule", name: "排期看板", path: "/schedule", icon: "Calendar" },
      { id: "tasks", name: "任务中心", path: "/tasks", icon: "ListTodo" },
    ],
  },
  {
    id: "pmo",
    label: "PMO 项目管理部",
    items: [
      {
        id: "pmo-dashboard",
        name: "PMO 驾驶舱",
        path: "/pmo/dashboard",
        icon: "LayoutDashboard",
      },
      {
        id: "pmo-initiations",
        name: "立项管理",
        path: "/pmo/initiations",
        icon: "FileText",
      },
      {
        id: "pmo-phases",
        name: "阶段管理",
        path: "/pmo/phases",
        icon: "Target",
      },
      {
        id: "pmo-risks",
        name: "风险管理",
        path: "/pmo/risks",
        icon: "AlertTriangle",
      },
      {
        id: "pmo-risk-wall",
        name: "风险预警墙",
        path: "/pmo/risk-wall",
        icon: "AlertTriangle",
      },
      {
        id: "pmo-closure",
        name: "项目结项",
        path: "/pmo/closure",
        icon: "CheckCircle2",
      },
      {
        id: "project-reviews",
        name: "项目复盘",
        path: "/projects/reviews",
        icon: "FileText",
      },
      {
        id: "lessons-learned",
        name: "经验教训库",
        path: "/projects/lessons-learned",
        icon: "BookOpen",
      },
      {
        id: "best-practices",
        name: "最佳实践推荐",
        path: "/projects/best-practices/recommend",
        icon: "Sparkles",
      },
      {
        id: "pmo-resource",
        name: "资源总览",
        path: "/pmo/resource-overview",
        icon: "Users",
      },
      {
        id: "pmo-meetings",
        name: "会议管理",
        path: "/pmo/meetings",
        icon: "Calendar",
      },
      {
        id: "pmo-weekly",
        name: "项目周报",
        path: "/pmo/weekly-report",
        icon: "BarChart3",
      },
    ],
  },
  {
    id: "sales",
    label: "销售管理",
    items: [
      {
        id: "sales-dashboard",
        name: "销售工作台",
        path: "/sales-dashboard",
        icon: "LayoutDashboard",
      },
      {
        id: "sales-director-dashboard",
        name: "销售总监工作台",
        path: "/sales-director-dashboard",
        icon: "LayoutDashboard",
      },
      { id: "leads", name: "线索管理", path: "/sales/leads", icon: "Target" },
      {
        id: "opportunities",
        name: "商机管理",
        path: "/sales/opportunities",
        icon: "TrendingUp",
      },
      {
        id: "customers",
        name: "客户管理",
        path: "/sales/customers",
        icon: "Building2",
      },
      {
        id: "quotes",
        name: "报价管理",
        path: "/sales/quotes",
        icon: "FileText",
      },
      {
        id: "contracts",
        name: "合同管理",
        path: "/sales/contracts",
        icon: "FileText",
      },
      {
        id: "invoices",
        name: "发票管理",
        path: "/sales/invoices",
        icon: "Receipt",
      },
      {
        id: "collections",
        name: "回款管理",
        path: "/sales/collections",
        icon: "DollarSign",
      },
    ],
  },
  {
    id: "presales",
    label: "售前技术",
    items: [
      {
        id: "presales-dashboard",
        name: "售前工作台",
        path: "/presales-dashboard",
        icon: "LayoutDashboard",
      },
      {
        id: "tech-assessments",
        name: "技术评估",
        path: "/presales/assessments",
        icon: "ClipboardCheck",
      },
      {
        id: "tech-reviews",
        name: "技术评审",
        path: "/technical-reviews",
        icon: "FileCheck",
      },
      {
        id: "solutions",
        name: "方案设计",
        path: "/presales/solutions",
        icon: "Lightbulb",
      },
    ],
  },
  {
    id: "procurement",
    label: "采购管理",
    items: [
      {
        id: "procurement-dashboard",
        name: "采购工作台",
        path: "/procurement-dashboard",
        icon: "LayoutDashboard",
      },
      {
        id: "purchases",
        name: "采购订单",
        path: "/purchases",
        icon: "ShoppingCart",
      },
      {
        id: "purchase-material-costs",
        name: "物料成本管理",
        path: "/sales/purchase-material-costs",
        icon: "DollarSign",
      },
      {
        id: "suppliers",
        name: "供应商管理",
        path: "/suppliers",
        icon: "Building2",
      },
      { id: "shortage", name: "缺料管理", path: "/shortage", icon: "Package" },
      { id: "arrivals", name: "到货跟踪", path: "/arrivals", icon: "Truck" },
    ],
  },
  {
    id: "production",
    label: "生产管理",
    items: [
      {
        id: "production-dashboard",
        name: "生产工作台",
        path: "/production-dashboard",
        icon: "LayoutDashboard",
      },
      {
        id: "manufacturing-director-dashboard",
        name: "制造总监工作台",
        path: "/manufacturing-director-dashboard",
        icon: "LayoutDashboard",
      },
      {
        id: "kit-check",
        name: "齐套检查",
        path: "/kit-check",
        icon: "CheckCircle2",
      },
      {
        id: "material-analysis",
        name: "齐套分析",
        path: "/material-analysis",
        icon: "Package",
      },
      {
        id: "assembly-kit",
        name: "装配齐套",
        path: "/assembly-kit",
        icon: "Wrench",
      },
      {
        id: "assembly-tasks",
        name: "装配任务",
        path: "/assembly-tasks",
        icon: "Wrench",
      },
    ],
  },
  {
    id: "delivery",
    label: "发货管理",
    items: [
      {
        id: "delivery-plan",
        name: "发货计划",
        path: "/pmc/delivery-plan",
        icon: "Calendar",
      },
      {
        id: "delivery-orders",
        name: "发货订单",
        path: "/pmc/delivery-orders",
        icon: "Truck",
      },
      {
        id: "pending-delivery",
        name: "待发货",
        path: "/pmc/delivery-orders?status=pending",
        icon: "Package",
      },
      {
        id: "in-transit",
        name: "在途订单",
        path: "/pmc/delivery-orders?status=in_transit",
        icon: "Truck",
      },
    ],
  },
  {
    id: "quality",
    label: "质量验收",
    items: [
      {
        id: "acceptance",
        name: "验收管理",
        path: "/acceptance",
        icon: "ClipboardList",
      },
      {
        id: "installation-dispatch",
        name: "安装调试派工",
        path: "/installation-dispatch",
        icon: "Settings",
      },
    ],
  },
  {
    id: "alerts",
    label: "监控与预警",
    items: [
      {
        id: "alerts",
        name: "预警中心",
        path: "/alerts",
        icon: "AlertTriangle",
      },
      { id: "issues", name: "问题管理", path: "/issues", icon: "AlertCircle" },
      {
        id: "issue-templates",
        name: "问题模板管理",
        path: "/issue-templates",
        icon: "FileText",
      },
      {
        id: "approvals",
        name: "审批中心",
        path: "/approvals",
        icon: "ClipboardCheck",
      },
      {
        id: "key-decisions",
        name: "决策事项",
        path: "/key-decisions",
        icon: "Crown",
      },
    ],
  },
  {
    id: "staff-matching",
    label: "AI人员匹配",
    items: [
      {
        id: "staff-tags",
        name: "标签字典",
        path: "/staff-matching/tags",
        icon: "Target",
      },
      {
        id: "staff-profiles",
        name: "员工档案",
        path: "/staff-matching/profiles",
        icon: "Users",
      },
      {
        id: "staffing-needs",
        name: "人员需求",
        path: "/staff-matching/staffing-needs",
        icon: "ClipboardList",
      },
      {
        id: "smart-matching",
        name: "智能匹配",
        path: "/staff-matching/matching",
        icon: "Sparkles",
      },
    ],
  },
  {
    id: "organization",
    label: "组织管理",
    items: [
      {
        id: "departments",
        name: "部门管理",
        path: "/departments",
        icon: "Building2",
      },
      { id: "employees", name: "人员管理", path: "/employees", icon: "Users" },
      {
        id: "performance",
        name: "绩效管理",
        path: "/performance",
        icon: "Award",
      },
      {
        id: "qualifications",
        name: "任职资格管理",
        path: "/qualifications",
        icon: "Award",
      },
    ],
  },
  {
    id: "finance",
    label: "财务管理",
    items: [
      {
        id: "finance-dashboard",
        name: "财务工作台",
        path: "/finance-manager-dashboard",
        icon: "LayoutDashboard",
      },
      {
        id: "financial-costs",
        name: "财务成本上传",
        path: "/financial-costs",
        icon: "DollarSign",
      },
      { id: "costs", name: "成本核算", path: "/costs", icon: "Calculator" },
      {
        id: "payment-approval",
        name: "付款审批",
        path: "/payment-approval",
        icon: "ClipboardCheck",
      },
      {
        id: "settlement",
        name: "项目结算",
        path: "/settlement",
        icon: "FileText",
      },
      {
        id: "financial-reports",
        name: "财务报表",
        path: "/financial-reports",
        icon: "BarChart3",
      },
    ],
  },
  {
    id: "customer-service",
    label: "客服管理",
    items: [
      {
        id: "cs-dashboard",
        name: "客服工作台",
        path: "/customer-service-dashboard",
        icon: "LayoutDashboard",
      },
      {
        id: "service-tickets",
        name: "服务工单",
        path: "/service-tickets",
        icon: "FileText",
      },
      {
        id: "service-records",
        name: "服务记录",
        path: "/service-records",
        icon: "ClipboardCheck",
      },
      {
        id: "customer-communications",
        name: "客户沟通",
        path: "/customer-communications",
        icon: "MessageSquare",
      },
      {
        id: "customer-satisfaction",
        name: "满意度调查",
        path: "/customer-satisfaction",
        icon: "Star",
      },
      {
        id: "service-analytics",
        name: "服务分析",
        path: "/service-analytics",
        icon: "BarChart3",
      },
      {
        id: "service-knowledge-base",
        name: "知识库",
        path: "/service-knowledge-base",
        icon: "BookOpen",
      },
    ],
  },
  {
    id: "personal",
    label: "个人中心",
    items: [
      {
        id: "notifications",
        name: "通知中心",
        path: "/notifications",
        icon: "Bell",
      },
      { id: "punch-in", name: "岗位打卡", path: "/punch-in", icon: "Clock" },
      { id: "timesheet", name: "工时填报", path: "/timesheet", icon: "Clock" },
      {
        id: "timesheet-dashboard",
        name: "工时统计",
        path: "/timesheet/dashboard",
        icon: "BarChart3",
      },
      {
        id: "timesheet-batch",
        name: "批量操作",
        path: "/timesheet/batch",
        icon: "CheckSquare",
      },
      {
        id: "my-performance",
        name: "我的绩效",
        path: "/personal/my-performance",
        icon: "Award",
      },
      {
        id: "my-bonus",
        name: "我的奖金",
        path: "/personal/my-bonus",
        icon: "DollarSign",
      },
      {
        id: "monthly-summary",
        name: "月度总结",
        path: "/personal/monthly-summary",
        icon: "FileText",
      },
      {
        id: "knowledge",
        name: "知识管理",
        path: "/settings?section=knowledge",
        icon: "BookOpen",
      },
      { id: "settings", name: "个人设置", path: "/settings", icon: "Settings" },
    ],
  },
  {
    id: "system",
    label: "系统管理",
    items: [
      {
        id: "user-management",
        name: "用户管理",
        path: "/user-management",
        icon: "Users",
      },
      {
        id: "role-management",
        name: "角色管理",
        path: "/role-management",
        icon: "Shield",
      },
      {
        id: "project-role-types",
        name: "项目角色类型",
        path: "/project-role-types",
        icon: "UserCog",
      },
    ],
  },
  {
    id: "master-data",
    label: "主数据管理",
    items: [
      {
        id: "customer-management",
        name: "客户管理",
        path: "/customer-management",
        icon: "Building2",
      },
      {
        id: "supplier-management-data",
        name: "供应商管理",
        path: "/supplier-management-data",
        icon: "Truck",
      },
      {
        id: "department-management",
        name: "部门管理",
        path: "/department-management",
        icon: "Building2",
      },
    ],
  },
];

// 获取所有菜单项的扁平列表（用于快速查找）
export const getAllMenuItems = () => {
  const items = [];
  allMenuGroups.forEach((group) => {
    group.items.forEach((item) => {
      items.push({
        ...item,
        groupId: group.id,
        groupLabel: group.label,
      });
    });
  });
  return items;
};

// 根据选中的菜单ID列表构建导航组
export const buildNavGroupsFromSelection = (selectedMenuIds) => {
  if (!selectedMenuIds || selectedMenuIds.length === 0) {
    return [];
  }

  const navGroups = [];

  allMenuGroups.forEach((group) => {
    const selectedItems = group.items.filter((item) =>
      selectedMenuIds.includes(item.id),
    );

    if (selectedItems.length > 0) {
      navGroups.push({
        label: group.label,
        items: selectedItems.map((item) => ({
          name: item.name,
          path: item.path,
          icon: item.icon,
        })),
      });
    }
  });

  return navGroups;
};

// 从导航组提取菜单ID列表
export const extractMenuIdsFromNavGroups = (navGroups) => {
  if (!navGroups || navGroups.length === 0) {
    return [];
  }

  const menuIds = [];
  const allItems = getAllMenuItems();

  navGroups.forEach((group) => {
    if (group.items) {
      group.items.forEach((item) => {
        // 通过 path 匹配找到对应的菜单ID
        const found = allItems.find((menuItem) => menuItem.path === item.path);
        if (found) {
          menuIds.push(found.id);
        }
      });
    }
  });

  return menuIds;
};

// 默认的管理员菜单（所有菜单）
export const getDefaultAdminMenuIds = () => {
  return getAllMenuItems().map((item) => item.id);
};

// 默认的普通用户菜单
export const getDefaultUserMenuIds = () => {
  return ["workstation", "tasks", "notifications", "timesheet", "settings"];
};
