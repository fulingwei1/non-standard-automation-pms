/**
 * 默认导航组配置
 * 用于管理员和通用场景
 *
 * permission: 访问该菜单所需的权限码
 * permissionLabel: 无权限时显示的提示文字
 */

export const defaultNavGroups = [
  // 1. 概览
  {
    label: "概览",
    items: [
      { name: "工作台", path: "/dashboard", icon: "LayoutDashboard", badge: null },
      { name: "运营大屏", path: "/operation", icon: "BarChart3", permission: "operation:dashboard:read", permissionLabel: "运营大屏" },
      { name: "预警管理", path: "/alerts", icon: "AlertTriangle", badge: "3", permission: "alert:read", permissionLabel: "预警管理" },
      { name: "问题异常", path: "/issues", icon: "AlertCircle", permission: "issue:read", permissionLabel: "问题异常" },
      { name: "绩效评价", path: "/evaluation-tasks", icon: "ListTodo", permission: "evaluation:task:read", permissionLabel: "绩效评价" },
      { name: "通知中心", path: "/notifications", icon: "Bell", badge: "5" },
      { name: "审批中心", path: "/approvals", icon: "ClipboardCheck", badge: "2", permission: "approval:read", permissionLabel: "审批查看" },
      { name: "知识文档", path: "/knowledge-base", icon: "BookOpen", permission: "knowledge:read", permissionLabel: "知识文档" }
    ]
  },
    {
    label: "战略管理",
    items: [
      { name: "决策驾驶舱", path: "/executive-dashboard", icon: "Gauge", permission: "executive:dashboard:read", permissionLabel: "决策驾驶舱" },
      { name: "战略分析", path: "/strategy", icon: "Target", permission: "strategy:dashboard:read", permissionLabel: "战略分析" },
      { name: "战略地图", path: "/strategy/map", icon: "Map", permission: "strategy:dashboard:read", permissionLabel: "战略地图" },
      { name: "CSF 管理", path: "/strategy/csf", icon: "Layers", permission: "strategy:csf:read", permissionLabel: "CSF 管理" },
      { name: "KPI 管理", path: "/strategy/kpi", icon: "Activity", permission: "strategy:kpi:read", permissionLabel: "KPI 管理" },
      { name: "年度重点工作", path: "/strategy/annual-work", icon: "Briefcase", permission: "strategy:annual-work:read", permissionLabel: "年度重点工作" },
      { name: "目标分解", path: "/strategy/decomposition", icon: "GitBranch", permission: "strategy:decomposition:read", permissionLabel: "目标分解" },
      { name: "战略日历", path: "/strategy/calendar", icon: "Calendar", permission: "strategy:calendar:read", permissionLabel: "战略日历" },
      { name: "同比分析", path: "/strategy/comparison", icon: "TrendingUp", permission: "strategy:comparison:read", permissionLabel: "同比分析" },
      { name: "关键决策", path: "/key-decisions", icon: "Lightbulb", permission: "executive:decision:read", permissionLabel: "关键决策" },
      { name: "管理节拍", path: "/management-rhythm-dashboard", icon: "Activity", permission: "pmo:rhythm:read", permissionLabel: "管理节拍" }
    ]
  },
  // 2. 销售管理
  {
    label: "销售管理",
    items: [
      { name: "销售目标", path: "/sales/targets", icon: "Target", permission: "sales:target:read", permissionLabel: "销售目标" },
      { name: "线索管理", path: "/sales/leads", icon: "Users", permission: "sales:lead:read", permissionLabel: "线索查看" },
      { name: "商机管理", path: "/sales/opportunities", icon: "Target", permission: "sales:opportunity:read", permissionLabel: "商机管理" },
      { name: "客户管理", path: "/customers", icon: "Building2", permission: "customer:read", permissionLabel: "客户查看" },
      { name: "销售漏斗", path: "/sales-funnel", icon: "TrendingDown", permission: "sales:funnel:read", permissionLabel: "销售漏斗" },
      { name: "销售团队", path: "/sales-team", icon: "Users", permission: "sales:team:read", permissionLabel: "销售团队" },
      { name: "投标管理", path: "/bidding", icon: "Target", permission: "sales:bid:read", permissionLabel: "投标管理" },
      { name: "合同管理", path: "/sales/contracts", icon: "FileCheck", permission: "sales:contract:read", permissionLabel: "合同管理" },
      { name: "应收账款", path: "/sales/receivables", icon: "CreditCard", permission: "finance:receivable:read", permissionLabel: "应收账款" },
      { name: "发票管理", path: "/invoices", icon: "Receipt", permission: "finance:invoice:read", permissionLabel: "发票管理" }
    ]
  },
  // 4. 售前技术
  {
    label: "售前技术",
    items: [
      { name: "方案评审", path: "/presales-tasks", icon: "ListTodo", permission: "presales:task:read", permissionLabel: "方案评审" },
      { name: "项目立项", path: "/pmo/initiations", icon: "FileText", permission: "project:initiation:read", permissionLabel: "立项管理" },
      { name: "报价管理", path: "/cost-quotes/quotes", icon: "Calculator", permission: "sales:quote:read", permissionLabel: "报价管理" }
    ]
  },
  // 5. 项目管理
  {
    label: "项目管理",
    items: [
      { name: "项目列表", path: "/projects", icon: "List", permission: "project:project:read", permissionLabel: "项目列表" },
      { name: "预算管理", path: "/budgets", icon: "CreditCard", permission: "budget:read", permissionLabel: "预算管理" },
      { name: "项目看板", path: "/board", icon: "Kanban", permission: "project:project:read", permissionLabel: "项目看板" },
      { name: "甘特图", path: "/gantt", icon: "GitBranch", permission: "project:read", permissionLabel: "甘特图" },
      { name: "ECN变更", path: "/ecn", icon: "FileText", permission: "project:read", permissionLabel: "ECN变更" },
      { name: "现场调试", path: "/field-commissioning", icon: "Wrench", permission: "project:read", permissionLabel: "现场调试" },
      { name: "项目结项", path: "/pmo/closure", icon: "CheckCircle2", permission: "project:close", permissionLabel: "项目结项" },
      { name: "项目复盘", path: "/projects/reviews", icon: "FileText", permission: "project_review:read", permissionLabel: "项目复盘" },
      { name: "经验教训", path: "/lessons-learned", icon: "BookOpen", permission: "project:read", permissionLabel: "经验教训" },
      { name: "资源全景", path: "/resource-overview", icon: "Users", permission: "project:project:read", permissionLabel: "资源全景" }
    ]
  },
  // 6. 工程技术
  {
    label: "工程技术",
    items: [
      { name: "ECN管理", path: "/change-management/ecn", icon: "FileText", permission: "ecn:read", permissionLabel: "ECN管理" },
      { name: "ECN类型", path: "/change-management/ecn-types", icon: "Layers", permission: "ecn:type:read", permissionLabel: "ECN类型" },
      { name: "ECN统计", path: "/change-management/ecn/statistics", icon: "BarChart3", permission: "ecn:statistics:read", permissionLabel: "ECN统计" },
      { name: "技术评审", path: "/technical-reviews", icon: "FileCheck", permission: "technical:review:read", permissionLabel: "技术评审" }
    ]
  },
  // 7. 研发管理
  {
    label: "研发管理",
    items: [
      { name: "研发项目", path: "/rd-projects", icon: "Briefcase", permission: "rd:project:read", permissionLabel: "研发项目" },
      { name: "研发成本", path: "/rd-cost", icon: "DollarSign", permission: "rd:cost:read", permissionLabel: "研发成本" }
    ]
  },
  // 8. 采购管理
  {
    label: "采购管理",
    items: [
      { name: "采购订单", path: "/purchases", icon: "ShoppingCart", permission: "purchase:read", permissionLabel: "采购订单" },
      { name: "采购申请", path: "/purchase-requests", icon: "FileText", permission: "purchase:request:read", permissionLabel: "采购申请" },
      { name: "供应商管理", path: "/suppliers", icon: "Building2", permission: "supplier:read", permissionLabel: "供应商管理" },
      { name: "BOM管理", path: "/bom", icon: "Layers", permission: "bom:read", permissionLabel: "BOM管理" },
      { name: "物料管理", path: "/materials", icon: "Package", permission: "material:read", permissionLabel: "物料管理" },
      { name: "物料需求", path: "/material-demands", icon: "List", permission: "material:demand:read", permissionLabel: "物料需求" },
      { name: "收货管理", path: "/purchases/receipts", icon: "Truck", permission: "purchase:receipt:read", permissionLabel: "收货管理" },
      { name: "齐套缺料", path: "/material-analysis", icon: "Boxes", permission: "material:analysis:read", permissionLabel: "齐套缺料" },
      { name: "价格趋势", path: "/supplier-price", icon: "TrendingUp", permission: "purchase:read", permissionLabel: "价格趋势" },
      { name: "采购分析", path: "/procurement-analysis", icon: "BarChart3", permission: "purchase:analysis:read", permissionLabel: "采购分析" }
    ]
  },
  // 9. 生产管理
  {
    label: "生产管理",
    items: [
      { name: "生产看板", path: "/production-board", icon: "Kanban", permission: "production:board:read", permissionLabel: "生产看板" },
      { name: "工单管理", path: "/work-orders", icon: "ClipboardList", permission: "workorder:read", permissionLabel: "工单管理" },
      { name: "派工管理", path: "/dispatch-management", icon: "Users", permission: "dispatch:read", permissionLabel: "派工管理" },
      { name: "生产计划", path: "/production-plans", icon: "Calendar", permission: "production:plan:read", permissionLabel: "生产计划" },
      { name: "装配任务", path: "/assembly-tasks", icon: "Wrench", permission: "assembly:task:read", permissionLabel: "装配任务" },
      { name: "领料管理", path: "/material-requisitions", icon: "Package", permission: "material:requisition:read", permissionLabel: "领料管理" },
      { name: "生产异常", path: "/production-exceptions", icon: "AlertCircle", permission: "production:exception:read", permissionLabel: "生产异常" },
      { name: "车间管理", path: "/workshops", icon: "Building2", permission: "workshop:read", permissionLabel: "车间管理" },
      { name: "工人管理", path: "/workers", icon: "Users", permission: "worker:read", permissionLabel: "工人管理" },
      { name: "外协订单", path: "/outsourcing-orders", icon: "Truck", permission: "outsourcing:read", permissionLabel: "外协订单" }
    ]
  },
  // 10. 发货管理
  {
    label: "发货管理",
    items: [
      { name: "发货管理", path: "/pmc/delivery-orders", icon: "Truck", permission: "delivery:order:read", permissionLabel: "发货管理" }
    ]
  },
  // 11. 客服验收
  {
    label: "客服验收",
    items: [
      { name: "服务工单", path: "/service-tickets", icon: "FileText", permission: "service:ticket:read", permissionLabel: "服务工单" },
      { name: "客户沟通", path: "/customer-communications", icon: "MessageSquare", permission: "customer:communication:read", permissionLabel: "客户沟通" },
      { name: "满意度调查", path: "/customer-satisfaction", icon: "Star", permission: "customer:satisfaction:read", permissionLabel: "满意度调查" },
      { name: "服务分析", path: "/service-analytics", icon: "BarChart3", permission: "service:analytics:read", permissionLabel: "服务分析" },
      { name: "验收管理", path: "/acceptance", icon: "ClipboardList", permission: "acceptance:read", permissionLabel: "验收管理" },
      { name: "安装调试", path: "/installation-dispatch", icon: "Settings", permission: "installation:read", permissionLabel: "安装调试" }
    ]
  },
  // 12. 财务管理
  {
    label: "财务分析",
    items: [
      { name: "成本核算", path: "/costs", icon: "Calculator", permission: "cost:accounting:read", permissionLabel: "成本核算" },
      { name: "付款审批", path: "/payment-approval", icon: "ClipboardCheck", permission: "payment:approve", permissionLabel: "付款审批" },
      { name: "项目结算", path: "/settlement", icon: "FileText", permission: "settlement:read", permissionLabel: "项目结算" },
      { name: "财务报表", path: "/financial-reports", icon: "BarChart3", permission: "finance:report:read", permissionLabel: "财务报表" },
      { name: "毛利率预测", path: "/margin-prediction", icon: "TrendingUp", permission: "cost:accounting:read", permissionLabel: "毛利率预测" },
      { name: "成本归集", path: "/cost-collection", icon: "ArrowDownToLine", permission: "cost:accounting:read", permissionLabel: "成本归集" },
      { name: "报价对比", path: "/quote-compare", icon: "ArrowLeftRight", permission: "cost:accounting:read", permissionLabel: "报价对比" },
      { name: "成本偏差", path: "/cost-variance", icon: "AlertTriangle", permission: "cost:accounting:read", permissionLabel: "成本偏差分析" },
      { name: "人工成本", path: "/labor-cost", icon: "Users", permission: "cost:accounting:read", permissionLabel: "人工成本明细" },
      { name: "多币种", path: "/multi-currency", icon: "Coins", permission: "finance:read", permissionLabel: "多币种管理" }
    ],
    roles: ["finance", "accounting", "财务", "会计", "admin", "super_admin"]
  },
  // 13. 人力资源
  {
    label: "人力资源",
    items: [
      { name: "绩效管理", path: "/performance", icon: "TrendingUp", permission: "performance:manage", permissionLabel: "绩效管理" },
      { name: "资质管理", path: "/qualifications", icon: "Award", permission: "qualification:read", permissionLabel: "资质管理" },
      { name: "评价配置", path: "/evaluation-weight-config", icon: "Settings", permission: "evaluation:config:manage", permissionLabel: "评价配置" },
      { name: "标签管理", path: "/staff-matching/tags", icon: "Layers", permission: "staff:tag:manage", permissionLabel: "标签管理" },
      { name: "员工档案", path: "/staff-matching/profiles", icon: "Users", permission: "staff:profile:read", permissionLabel: "员工档案" },
      { name: "人员需求", path: "/staff-matching/staffing-needs", icon: "Target", permission: "staff:need:read", permissionLabel: "人员需求" },
      { name: "AI智能匹配", path: "/staff-matching/matching", icon: "Sparkles", permission: "staff:match:read", permissionLabel: "AI匹配" }
    ]
  },
  // 14. 个人中心
  {
    label: "个人中心",
    items: [
      { name: "工时填报", path: "/timesheet", icon: "Clock" },
      { name: "我的绩效", path: "/personal/my-performance", icon: "TrendingUp" },
      { name: "工程师绩效", path: "/engineer-performance", icon: "Gauge", permission: "performance:engineer:read", permissionLabel: "工程师绩效" },
      { name: "工程师协作", path: "/engineer-performance/collaboration", icon: "Users", permission: "engineer:collaboration:read", permissionLabel: "工程师协作" },
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  },
  // 16. 系统管理
  {
    label: "系统管理",
    items: [
      { name: "阶段模板", path: "/stage-templates", icon: "Layers", permission: "system:template:manage", permissionLabel: "阶段模板" },
      { name: "用户管理", path: "/user-management", icon: "Users", permission: "USER_VIEW", permissionLabel: "用户管理" },
      { name: "角色管理", path: "/role-management", icon: "Shield", permission: "ROLE_VIEW", permissionLabel: "角色管理" },
      { name: "权限管理", path: "/permission-management", icon: "Key", permission: "ROLE_VIEW", permissionLabel: "权限管理" },
      { name: "组织管理", path: "/organization-management", icon: "Building2", permission: "system:org:manage", permissionLabel: "组织管理" },
      { name: "岗位管理", path: "/position-management", icon: "UserCog", permission: "system:position:manage", permissionLabel: "岗位管理" },
      { name: "定时任务", path: "/scheduler-monitoring", icon: "Activity", permission: "system:scheduler:read", permissionLabel: "定时任务" },
      { name: "审计日志", path: "/audit-logs", icon: "FileText", permission: "AUDIT_VIEW", permissionLabel: "审计日志" },
      { name: "数据导入导出", path: "/data-import-export", icon: "Archive", permission: "system:data:manage", permissionLabel: "数据导入导出" }
    ],
    roles: ["admin", "super_admin"]
  }
];
