/**
 * 角色导航配置
 * 根据角色返回对应的导航菜单
 */

/**
 * 获取角色的默认导航菜单
 * @param {string} role 角色代码
 * @returns {array} 导航组配置
 */
export function getNavForRole(role) {
  const navConfigs = {
    chairman: [
      {
        label: "战略决策",
        items: [
          {
            name: "董事长工作台",
            path: "/chairman-dashboard",
            icon: "LayoutDashboard",
          },
          { name: "战略分析", path: "/strategy/analysis", icon: "Target" },
        ],
      },
      {
        label: "全面监控",
        items: [
          { name: "项目看板", path: "/board", icon: "Kanban" },
          { name: "项目列表", path: "/projects", icon: "Briefcase" },
          { name: "运营大屏", path: "/operation", icon: "BarChart3" },
        ],
      },
      {
        label: "人员管理",
        items: [
          { name: "工程师绩效排名", path: "/engineer-performance/ranking", icon: "TrendingUp" },
        ],
      },
      {
        label: "重大事项",
        items: [
          { name: "审批中心", path: "/approvals", icon: "ClipboardCheck" },
          { name: "预警中心", path: "/alerts", icon: "AlertTriangle" },
        ],
      },
      {
        label: "个人中心",
        items: [
          { name: "通知中心", path: "/notifications", icon: "Bell" },
          { name: "知识管理", path: "/knowledge-base", icon: "BookOpen" },
          { name: "个人设置", path: "/settings", icon: "Settings" },
        ],
      },
    ],
    gm: [
      {
        label: "经营管理",
        items: [
          {
            name: "总经理工作台",
            path: "/gm-dashboard",
            icon: "LayoutDashboard",
          },
          { name: "运营大屏", path: "/operation", icon: "BarChart3" },
        ],
      },
      {
        label: "项目管理",
        items: [
          { name: "项目看板", path: "/board", icon: "Kanban" },
          { name: "项目列表", path: "/projects", icon: "Briefcase" },
          { name: "排期看板", path: "/schedule", icon: "Calendar" },
        ],
      },
      {
        label: "人员管理",
        items: [
          { name: "工程师绩效排名", path: "/engineer-performance/ranking", icon: "TrendingUp" },
        ],
      },
      {
        label: "审批与监控",
        items: [
          { name: "审批中心", path: "/approvals", icon: "ClipboardCheck" },
          { name: "预警中心", path: "/alerts", icon: "AlertTriangle" },
        ],
      },
      {
        label: "个人中心",
        items: [
          { name: "通知中心", path: "/notifications", icon: "Bell" },
          { name: "知识管理", path: "/knowledge-base", icon: "BookOpen" },
          { name: "个人设置", path: "/settings", icon: "Settings" },
        ],
      },
    ],
    VP: [
      {
        label: "经营管理",
        items: [
          {
            name: "副总工作台",
            path: "/gm-dashboard",
            icon: "LayoutDashboard",
          },
          { name: "运营大屏", path: "/operation", icon: "BarChart3" },
        ],
      },
      {
        label: "项目管理",
        items: [
          { name: "项目看板", path: "/board", icon: "Kanban" },
          { name: "项目列表", path: "/projects", icon: "Briefcase" },
          { name: "排期看板", path: "/schedule", icon: "Calendar" },
        ],
      },
      {
        label: "人员管理",
        items: [
          { name: "工程师绩效排名", path: "/engineer-performance/ranking", icon: "TrendingUp" },
        ],
      },
      {
        label: "审批与监控",
        items: [
          { name: "审批中心", path: "/approvals", icon: "ClipboardCheck" },
          { name: "预警中心", path: "/alerts", icon: "AlertTriangle" },
        ],
      },
      {
        label: "个人中心",
        items: [
          { name: "通知中心", path: "/notifications", icon: "Bell" },
          { name: "知识管理", path: "/knowledge-base", icon: "BookOpen" },
          { name: "个人设置", path: "/settings", icon: "Settings" },
        ],
      },
    ],
    sales_director: [
      {
        label: "团队管理",
        items: [
          {
            name: "销售总监工作台",
            path: "/sales-director-dashboard",
            icon: "LayoutDashboard",
          },
          { name: "销售团队管理", path: "/sales/team", icon: "Users" },
          { name: "销售目标", path: "/sales/targets", icon: "Target" },
        ],
      },
      {
        label: "销售监控",
        items: [
          { name: "销售统计", path: "/sales/statistics", icon: "BarChart3" },
          { name: "销售漏斗", path: "/sales/funnel", icon: "Target" },
          { name: "CPQ配置报价", path: "/sales/cpq", icon: "Calculator" },
          { name: "客户管理", path: "/sales/customers", icon: "Building2" },
          { name: "商机看板", path: "/opportunities", icon: "Target" },
        ],
      },
      {
        label: "审批与监控",
        items: [
          { name: "审批中心", path: "/approvals", icon: "ClipboardCheck" },
          { name: "预警中心", path: "/alerts", icon: "AlertTriangle" },
          { name: "问题管理", path: "/issues", icon: "AlertCircle" },
        ],
      },
      {
        label: "项目跟踪",
        items: [
          { name: "项目看板", path: "/board", icon: "Kanban" },
          { name: "项目列表", path: "/projects", icon: "Briefcase" },
        ],
      },
      {
        label: "个人中心",
        items: [
          { name: "通知中心", path: "/notifications", icon: "Bell" },
          {
            name: "知识管理",
            path: "/knowledge-base",
            icon: "BookOpen",
          },
          { name: "个人设置", path: "/settings", icon: "Settings" },
        ],
      },
    ],
    sales_manager: [
      {
        label: "销售工作",
        items: [
          {
            name: "销售工作台",
            path: "/sales-dashboard",
            icon: "LayoutDashboard",
          },
          { name: "客户管理", path: "/sales/customers", icon: "Building2" },
          { name: "商机管理", path: "/sales/opportunities", icon: "Target" },
        ],
      },
      {
        label: "销售业务",
        items: [
          { name: "线索评估", path: "/lead-assessment", icon: "Target" },
          { name: "报价管理", path: "/sales/quotes", icon: "Calculator" },
          { name: "CPQ配置报价", path: "/sales/cpq", icon: "Calculator" },
          { name: "合同管理", path: "/sales/contracts", icon: "FileCheck" },
          { name: "回款跟踪", path: "/payments", icon: "CreditCard" },
          { name: "应收账款", path: "/sales/receivables", icon: "CreditCard" },
        ],
      },
      {
        label: "团队管理",
        items: [
          { name: "团队业绩", path: "/sales/team/performance", icon: "Users" },
          { name: "团队统计", path: "/sales/statistics", icon: "BarChart3" },
          { name: "销售目标", path: "/sales/targets", icon: "Target" },
        ],
      },
      {
        label: "项目跟踪",
        items: [
          { name: "项目进度", path: "/sales-projects", icon: "Briefcase" },
          { name: "项目看板", path: "/board", icon: "Kanban" },
          { name: "项目列表", path: "/projects", icon: "Briefcase" },
        ],
      },
      {
        label: "审批与监控",
        items: [
          { name: "审批中心", path: "/approvals", icon: "ClipboardCheck" },
          { name: "预警中心", path: "/alerts", icon: "AlertTriangle" },
        ],
      },
      {
        label: "个人中心",
        items: [
          { name: "通知中心", path: "/notifications", icon: "Bell" },
          {
            name: "知识管理",
            path: "/knowledge-base",
            icon: "BookOpen",
          },
          { name: "个人设置", path: "/settings", icon: "Settings" },
        ],
      },
    ],
    // 默认配置（用于未定义专门菜单的角色）
    default_user: [
      {
        label: "概览",
        items: [
          { name: "工作台", path: "/workstation", icon: "LayoutDashboard" },
          { name: "运营大屏", path: "/operation", icon: "BarChart3" },
        ],
      },
      {
        label: "项目管理",
        items: [
          { name: "项目看板", path: "/board", icon: "Kanban" },
          { name: "排期看板", path: "/schedule", icon: "Calendar" },
          { name: "任务中心", path: "/tasks", icon: "ListTodo" },
        ],
      },
      {
        label: "团队管理",
        items: [
          { name: "工程师绩效排名", path: "/engineer-performance/ranking", icon: "TrendingUp" },
          { name: "审批中心", path: "/approvals", icon: "ClipboardCheck" },
          { name: "预警中心", path: "/alerts", icon: "AlertTriangle" },
        ],
      },
      {
        label: "个人中心",
        items: [
          { name: "通知中心", path: "/notifications", icon: "Bell" },
          { name: "知识管理", path: "/knowledge-base", icon: "BookOpen" },
          { name: "个人设置", path: "/settings", icon: "Settings" },
        ],
      },
    ],
    hr_manager: [
      {
        label: "人力资源",
        items: [
          {
            name: "人事工作台",
            path: "/hr-dashboard",
            icon: "LayoutDashboard",
          },
          { name: "人员管理", path: "/employees", icon: "Users" },
          { name: "绩效管理", path: "/performance", icon: "Award" },
        ],
      },
      {
        label: "个人中心",
        items: [
          { name: "通知中心", path: "/notifications", icon: "Bell" },
          { name: "知识管理", path: "/knowledge-base", icon: "BookOpen" },
          { name: "个人设置", path: "/settings", icon: "Settings" },
        ],
      },
    ],
  };

  return navConfigs[role] || navConfigs.default_user;
}
