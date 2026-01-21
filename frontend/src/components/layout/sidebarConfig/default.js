/**
 * 默认导航组配置
 * 用于管理员和通用场景
 *
 * permission: 访问该菜单所需的权限码
 * permissionLabel: 无权限时显示的提示文字
 */

export const defaultNavGroups = [
  // 1. 战略管理 (BEM)
  {
    label: "战略管理",
    items: [
      { name: "董事长工作台", path: "/chairman-dashboard", icon: "Crown", permission: "executive:chairman:dashboard", permissionLabel: "董事长工作台" },
      { name: "总经理工作台", path: "/gm-dashboard", icon: "Award", permission: "executive:gm:dashboard", permissionLabel: "总经理工作台" },
      { name: "战略仪表板", path: "/strategy", icon: "Target", permission: "strategy:dashboard:read", permissionLabel: "战略仪表板" },
      { name: "战略分析", path: "/strategy-analysis", icon: "BarChart3", permission: "strategy:analysis:read", permissionLabel: "战略分析" },
      { name: "关键决策", path: "/key-decisions", icon: "Lightbulb", permission: "executive:decision:read", permissionLabel: "关键决策" },
      { name: "管理节拍", path: "/management-rhythm-dashboard", icon: "Activity", permission: "pmo:rhythm:read", permissionLabel: "管理节拍" },
      { name: "战略会议", path: "/strategic-meetings", icon: "Target", permission: "meeting:strategic:read", permissionLabel: "战略会议" },
      { name: "会议地图", path: "/meeting-map", icon: "Kanban", permission: "meeting:map:read", permissionLabel: "会议地图" },
      { name: "会议报告", path: "/meeting-reports", icon: "FileText", permission: "meeting:report:read", permissionLabel: "会议报告" },
      { name: "决策驾驶舱", path: "/executive-dashboard", icon: "Gauge", permission: "executive:dashboard:read", permissionLabel: "决策驾驶舱" }
    ]
  },
  // 2. 概览
  {
    label: "概览",
    items: [
      { name: "工作台", path: "/dashboard", icon: "LayoutDashboard", badge: null },
      { name: "运营大屏", path: "/operation", icon: "BarChart3", permission: "operation:dashboard:read", permissionLabel: "运营大屏" },
      { name: "工作中心", path: "/work-center", icon: "LayoutDashboard", badge: null },
      { name: "预警中心", path: "/alerts", icon: "AlertTriangle", badge: "3", permission: "alert:read", permissionLabel: "预警查看" },
      { name: "问题管理", path: "/issues", icon: "AlertCircle", permission: "issue:read", permissionLabel: "问题查看" },
      { name: "通知中心", path: "/notifications", icon: "Bell", badge: "5" },
      { name: "审批中心", path: "/approvals", icon: "ClipboardCheck", badge: "2", permission: "approval:read", permissionLabel: "审批查看" },
      { name: "知识管理", path: "/knowledge-base", icon: "BookOpen" },
      { name: "文档中心", path: "/documents", icon: "FileText", permission: "document:read", permissionLabel: "文档查看" }
    ]
  },
  // 3. 销售管理
  {
    label: "销售管理",
    items: [
      { name: "客户管理", path: "/customers", icon: "Building2", permission: "customer:read", permissionLabel: "客户查看" },
      { name: "商机看板", path: "/opportunities", icon: "Target", permission: "sales:opportunity:read", permissionLabel: "商机查看" },
      { name: "商机管理", path: "/sales/opportunities", icon: "Target", permission: "sales:opportunity:read", permissionLabel: "商机管理" },
      { name: "线索管理", path: "/sales/leads", icon: "Users", permission: "sales:lead:read", permissionLabel: "线索查看" },
      { name: "线索评估", path: "/lead-assessment", icon: "CheckCircle2", permission: "sales:lead:assess", permissionLabel: "线索评估" },
      { name: "优先级管理", path: "/sales/priority", icon: "Star", permission: "sales:lead:update", permissionLabel: "线索管理" },
      { name: "销售漏斗", path: "/sales-funnel", icon: "TrendingDown", permission: "sales:funnel:read", permissionLabel: "销售漏斗" },
      { name: "销售团队", path: "/sales-team", icon: "Users", permission: "sales:team:read", permissionLabel: "销售团队" },
      { name: "销售目标", path: "/sales/targets", icon: "Target", permission: "sales:target:read", permissionLabel: "销售目标" },
      { name: "销售统计", path: "/sales/statistics", icon: "BarChart3", permission: "sales:statistics:read", permissionLabel: "销售统计" },
      { name: "销售报告", path: "/sales-reports", icon: "FileText", permission: "sales:report:read", permissionLabel: "销售报告" },
      { name: "合同管理", path: "/sales/contracts", icon: "FileCheck", permission: "sales:contract:read", permissionLabel: "合同查看" },
      { name: "合同审批", path: "/contract-approval", icon: "ClipboardCheck", permission: "sales:contract:approve", permissionLabel: "合同审批" },
      { name: "投标管理", path: "/bidding", icon: "Target", permission: "sales:bid:read", permissionLabel: "投标管理" },
      { name: "CPQ配置器", path: "/sales/cpq", icon: "Settings", permission: "sales:cpq:read", permissionLabel: "CPQ配置" },
      { name: "应收账款", path: "/sales/receivables", icon: "CreditCard", permission: "finance:receivable:read", permissionLabel: "应收账款" },
      { name: "回款跟踪", path: "/payments", icon: "CreditCard", permission: "finance:payment:read", permissionLabel: "回款查看" },
      { name: "发票管理", path: "/invoices", icon: "Receipt", permission: "finance:invoice:read", permissionLabel: "发票管理" },
      { name: "未中标分析", path: "/sales/loss-analysis", icon: "TrendingDown", permission: "sales:analysis:read", permissionLabel: "销售分析" },
      { name: "售前费用", path: "/sales/presale-expenses", icon: "DollarSign", permission: "sales:expense:read", permissionLabel: "费用查看" },
      { name: "断链分析", path: "/sales/pipeline-break-analysis", icon: "AlertTriangle", permission: "sales:analysis:read", permissionLabel: "销售分析" },
      { name: "归责分析", path: "/sales/accountability-analysis", icon: "Users", permission: "sales:analysis:read", permissionLabel: "销售分析" },
      { name: "健康度监控", path: "/sales/health-monitoring", icon: "Activity", permission: "sales:analysis:read", permissionLabel: "销售分析" },
      { name: "延期分析", path: "/sales/delay-analysis", icon: "Clock", permission: "sales:analysis:read", permissionLabel: "销售分析" },
      { name: "成本超支分析", path: "/sales/cost-overrun-analysis", icon: "DollarSign", permission: "sales:analysis:read", permissionLabel: "销售分析" },
      { name: "信息质量分析", path: "/sales/information-gap-analysis", icon: "FileText", permission: "sales:analysis:read", permissionLabel: "销售分析" }
    ]
  },
  // 3. 售前技术
  {
    label: "售前技术",
    items: [
      { name: "售前工作台", path: "/presales-dashboard", icon: "LayoutDashboard", permission: "presales:dashboard:read", permissionLabel: "售前工作台" },
      { name: "售前经理工作台", path: "/presales-manager-dashboard", icon: "Award", permission: "presales:manager:dashboard", permissionLabel: "售前经理工作台" },
      { name: "售前任务", path: "/presales-tasks", icon: "ListTodo", permission: "presales:task:read", permissionLabel: "售前任务" },
      { name: "方案中心", path: "/solutions", icon: "FileText", permission: "presales:solution:read", permissionLabel: "方案查看" },
      { name: "需求调研", path: "/requirement-survey", icon: "ClipboardList", permission: "presales:survey:read", permissionLabel: "需求调研" },
      { name: "报价管理", path: "/cost-quotes/quotes", icon: "Calculator", permission: "sales:quote:read", permissionLabel: "报价查看" },
      { name: "报价成本", path: "/cost-quotes/quote-costs", icon: "DollarSign", permission: "cost:quote:read", permissionLabel: "报价成本" },
      { name: "成本分析", path: "/cost-quotes/cost-analysis", icon: "BarChart3", permission: "cost:analysis:read", permissionLabel: "成本分析" },
      { name: "模板与CPQ", path: "/cost-quotes/templates", icon: "Layers", permission: "sales:quote:read", permissionLabel: "报价模板" }
    ]
  },
  // 5. 项目管理
  {
    label: "项目管理",
    items: [
      { name: "PMO 驾驶舱", path: "/pmo/dashboard", icon: "LayoutDashboard", permission: "pmo:dashboard:read", permissionLabel: "PMO驾驶舱" },
      { name: "项目列表", path: "/projects", icon: "List", permission: "project:project:read", permissionLabel: "项目查看" },
      { name: "项目阶段视图", path: "/stage-view", icon: "Workflow", permission: "project:stage:read", permissionLabel: "项目阶段查看" },
      { name: "项目阶段管理", path: "/pmo/phases", icon: "Layers", permission: "project:phase:manage", permissionLabel: "阶段管理" },
      { name: "立项管理", path: "/pmo/initiations", icon: "FileText", permission: "project:initiation:read", permissionLabel: "立项管理" },
      { name: "项目结项", path: "/pmo/closure", icon: "CheckCircle2", permission: "project:close", permissionLabel: "项目结项" },
      { name: "项目复盘", path: "/projects/reviews", icon: "FileText", permission: "project_review:read", permissionLabel: "项目复盘" },
      { name: "经验教训库", path: "/projects/lessons-learned", icon: "BookOpen", permission: "project:lesson:read", permissionLabel: "经验教训" },
      { name: "风险管理", path: "/pmo/risks", icon: "AlertTriangle", permission: "project:risk:manage", permissionLabel: "风险管理" },
      { name: "任务中心", path: "/progress-tracking/tasks", icon: "ListTodo", permission: "project:task:read", permissionLabel: "任务查看" },
      { name: "里程碑管理", path: "/progress-tracking/milestones", icon: "CheckCircle2", permission: "project:milestone:read", permissionLabel: "里程碑管理" },
      { name: "WBS管理", path: "/progress-tracking/wbs", icon: "Layers", permission: "project:wbs:read", permissionLabel: "WBS管理" },
      { name: "项目看板", path: "/progress-tracking/board", icon: "Kanban", permission: "project:project:read", permissionLabel: "项目查看" },
      { name: "排期看板", path: "/progress-tracking/schedule", icon: "Calendar", permission: "project:schedule:read", permissionLabel: "排期查看" },
      { name: "甘特图", path: "/progress-tracking/gantt", icon: "BarChart3", permission: "project:gantt:read", permissionLabel: "甘特图查看" },
      { name: "进度报告", path: "/progress-tracking/reports", icon: "FileText", permission: "project:progress:read", permissionLabel: "进度报告" },
      { name: "项目周报", path: "/pmo/weekly-report", icon: "BarChart3", permission: "project:report:read", permissionLabel: "项目报表" },
      { name: "风险预警", path: "/pmo/risk-wall", icon: "AlertTriangle", permission: "project:risk:read", permissionLabel: "风险预警" },
      { name: "资源总览", path: "/pmo/resource-overview", icon: "Users", permission: "resource:read", permissionLabel: "资源查看" },
      { name: "会议管理", path: "/pmo/meetings", icon: "Calendar", permission: "meeting:read", permissionLabel: "会议管理" },
      { name: "最佳实践", path: "/projects/best-practices/recommend", icon: "Sparkles", permission: "project:bestpractice:read", permissionLabel: "最佳实践" }
    ]
  },
  // 6. 工程技术
  {
    label: "工程技术",
    items: [
      { name: "工程师工作台", path: "/workstation", icon: "LayoutDashboard", permission: "engineer:workstation:read", permissionLabel: "工程师工作台" },
      { name: "ECN管理", path: "/change-management/ecn", icon: "FileText", permission: "ecn:read", permissionLabel: "ECN查看" },
      { name: "ECN类型", path: "/change-management/ecn-types", icon: "Layers", permission: "ecn:type:read", permissionLabel: "ECN类型" },
      { name: "逾期预警", path: "/change-management/ecn/overdue-alerts", icon: "AlertTriangle", permission: "ecn:alert:read", permissionLabel: "ECN预警" },
      { name: "ECN统计", path: "/change-management/ecn/statistics", icon: "BarChart3", permission: "ecn:statistics:read", permissionLabel: "ECN统计" },
      { name: "技术评审", path: "/technical-reviews", icon: "FileCheck", permission: "technical:review:read", permissionLabel: "技术评审" },
      { name: "技术规格", path: "/technical-spec", icon: "FileText", permission: "technical:spec:read", permissionLabel: "技术规格" },
      { name: "规格匹配检查", path: "/spec-match-check", icon: "CheckCircle2", permission: "technical:spec:match", permissionLabel: "规格匹配" },
      { name: "技术文档", path: "/technical-docs", icon: "BookOpen", permission: "technical:doc:read", permissionLabel: "技术文档" },
      { name: "工程师绩效仪表板", path: "/engineer-performance", icon: "Gauge", permission: "performance:engineer:read", permissionLabel: "工程师绩效" },
      { name: "工程师绩效排名", path: "/engineer-performance/ranking", icon: "TrendingUp", permission: "performance:read", permissionLabel: "绩效查看" },
      { name: "工程师协作", path: "/engineer-performance/collaboration", icon: "Users", permission: "engineer:collaboration:read", permissionLabel: "工程师协作" },
      { name: "工程师知识库", path: "/engineer-performance/knowledge", icon: "BookOpen", permission: "engineer:knowledge:read", permissionLabel: "工程师知识库" }
    ]
  },
  // 7. 研发管理
  {
    label: "研发管理",
    items: [
      { name: "研发项目列表", path: "/rd-projects", icon: "Briefcase", permission: "rd:project:read", permissionLabel: "研发项目" },
      { name: "研发成本录入", path: "/rd-cost-entry", icon: "DollarSign", permission: "rd:cost:create", permissionLabel: "研发成本录入" },
      { name: "研发成本汇总", path: "/rd-cost-summary", icon: "Calculator", permission: "rd:cost:read", permissionLabel: "研发成本汇总" },
      { name: "研发成本报告", path: "/rd-cost-reports", icon: "FileText", permission: "rd:cost:report", permissionLabel: "研发成本报告" }
    ]
  },
  // 8. 采购管理
  {
    label: "采购管理",
    items: [
      { name: "采购工作台", path: "/procurement-dashboard", icon: "LayoutDashboard", permission: "purchase:dashboard:read", permissionLabel: "采购工作台" },
      { name: "采购经理工作台", path: "/procurement-manager-dashboard", icon: "Award", permission: "purchase:manager:dashboard", permissionLabel: "采购经理工作台" },
      { name: "采购订单", path: "/purchases", icon: "ShoppingCart", permission: "purchase:read", permissionLabel: "采购订单查看" },
      { name: "采购申请", path: "/purchase-requests", icon: "FileText", permission: "purchase:request:read", permissionLabel: "采购申请查看" },
      { name: "从BOM生成订单", path: "/purchases/from-bom", icon: "Package", permission: "purchase:create", permissionLabel: "采购订单创建" },
      { name: "供应商管理", path: "/suppliers", icon: "Building2", permission: "supplier:read", permissionLabel: "��应商查看" },
      { name: "BOM管理", path: "/bom", icon: "Layers", permission: "bom:read", permissionLabel: "BOM查看" },
      { name: "物料管理", path: "/materials", icon: "Package", permission: "material:read", permissionLabel: "物料查看" },
      { name: "物料跟踪", path: "/material-tracking", icon: "Package", permission: "material:track:read", permissionLabel: "物料跟踪" },
      { name: "物料需求汇总", path: "/material-demands", icon: "List", permission: "material:demand:read", permissionLabel: "物料需求" },
      { name: "收货管理", path: "/purchases/receipts", icon: "Truck", permission: "purchase:receipt:read", permissionLabel: "收货管理" },
      { name: "到货跟踪", path: "/arrivals", icon: "Truck", permission: "purchase:arrival:read", permissionLabel: "到货跟踪" },
      { name: "缺料管理", path: "/shortage", icon: "Package", permission: "material:shortage:read", permissionLabel: "缺料管理" },
      { name: "物料齐套", path: "/material-readiness", icon: "CheckCircle2", permission: "material:readiness:read", permissionLabel: "物料齐套" },
      { name: "齐套分析", path: "/material-analysis", icon: "Boxes", permission: "material:analysis:read", permissionLabel: "齐套分析" },
      { name: "齐套率看板", path: "/kit-rate", icon: "Gauge", permission: "material:kit:read", permissionLabel: "齐套率" },
      { name: "缺料预警", path: "/shortage-alert", icon: "AlertTriangle", permission: "material:shortage:read", permissionLabel: "缺料预警" },
      { name: "采购分析", path: "/procurement-analysis", icon: "BarChart3", permission: "purchase:analysis:read", permissionLabel: "采购分析" },
      { name: "库存分析", path: "/inventory-analysis", icon: "Boxes", permission: "inventory:analysis:read", permissionLabel: "库存分析" },
      { name: "BOM装配配置", path: "/bom-assembly-attrs", icon: "Settings", permission: "bom:config:manage", permissionLabel: "BOM配置管理" },
      { name: "物料成本", path: "/cost-quotes/material-costs", icon: "DollarSign", permission: "cost:material:read", permissionLabel: "物料成本查看" },
      { name: "预算管理", path: "/budgets", icon: "CreditCard", permission: "budget:read", permissionLabel: "预算查看" }
    ]
  },
  // 9. 生产管理
  {
    label: "生产管理",
    items: [
      { name: "制造总监工作台", path: "/manufacturing-director-dashboard", icon: "LayoutDashboard", permission: "production:director:dashboard", permissionLabel: "总监工作台" },
      { name: "生产经理工作台", path: "/production-manager-dashboard", icon: "Award", permission: "production:manager:dashboard", permissionLabel: "生产经理工作台" },
      { name: "生产工作台", path: "/production-dashboard", icon: "LayoutDashboard", permission: "production:dashboard:read", permissionLabel: "生产工作台" },
      { name: "工人工作台", path: "/worker-workstation", icon: "Wrench", permission: "worker:workstation:read", permissionLabel: "工人工作台" },
      { name: "生产看板", path: "/production-board", icon: "Kanban", permission: "production:board:read", permissionLabel: "生产看板" },
      { name: "工单管理", path: "/work-orders", icon: "ClipboardList", permission: "workorder:read", permissionLabel: "工单查看" },
      { name: "派工管理", path: "/dispatch-management", icon: "Users", permission: "dispatch:read", permissionLabel: "派工管理" },
      { name: "生产计划", path: "/production-plans", icon: "Calendar", permission: "production:plan:read", permissionLabel: "生产计划" },
      { name: "工作报告", path: "/work-reports", icon: "FileText", permission: "work:report:read", permissionLabel: "工作报告" },
      { name: "装配任务", path: "/assembly-tasks", icon: "Wrench", permission: "assembly:task:read", permissionLabel: "装配任务" },
      { name: "装配齐套", path: "/assembly-kit", icon: "Wrench", permission: "assembly:kit:read", permissionLabel: "装配齐套" },
      { name: "齐套检查", path: "/kit-check", icon: "CheckCircle2", permission: "material:kit:read", permissionLabel: "齐套检查" },
      { name: "领料管理", path: "/material-requisitions", icon: "Package", permission: "material:requisition:read", permissionLabel: "领料管理" },
      { name: "生产异常", path: "/production-exceptions", icon: "AlertCircle", permission: "production:exception:read", permissionLabel: "生产异常" },
      { name: "车间管理", path: "/workshops", icon: "Building2", permission: "workshop:read", permissionLabel: "车间管理" },
      { name: "工人管理", path: "/workers", icon: "Users", permission: "worker:read", permissionLabel: "工人管理" },
      { name: "工作量看板", path: "/workload-board", icon: "Gauge", permission: "workload:read", permissionLabel: "工作量看板" },
      { name: "外协订单", path: "/outsourcing-orders", icon: "Truck", permission: "outsourcing:read", permissionLabel: "外协订单" },
      { name: "缺料管理看板", path: "/shortage-management-board", icon: "AlertTriangle", permission: "shortage:board:read", permissionLabel: "缺料看板" },
      { name: "缺料报告", path: "/shortage-reports", icon: "FileText", permission: "shortage:report:read", permissionLabel: "缺料报告" },
      { name: "到货跟踪", path: "/arrival-tracking", icon: "Truck", permission: "arrival:track:read", permissionLabel: "到货跟踪" },
      { name: "项目进度", path: "/sales-projects", icon: "Briefcase", permission: "project:project:read", permissionLabel: "项目查看" }
    ]
  },
  // 10. 发货管理
  {
    label: "发货管理",
    items: [
      { name: "发货计划", path: "/pmc/delivery-plan", icon: "Calendar", permission: "delivery:plan:read", permissionLabel: "发货计划" },
      { name: "发货订单", path: "/pmc/delivery-orders", icon: "Truck", permission: "delivery:order:read", permissionLabel: "发货订单" },
      { name: "待发货", path: "/pmc/delivery-orders?status=pending", icon: "Package", permission: "delivery:order:read", permissionLabel: "发货订单" },
      { name: "在途订单", path: "/pmc/delivery-orders?status=in_transit", icon: "Truck", permission: "delivery:order:read", permissionLabel: "发货订单" },
      { name: "出货管理", path: "/shipments", icon: "Package", permission: "shipment:read", permissionLabel: "出货管理" }
    ]
  },
  // 11. 客服验收
  {
    label: "客服验收",
    items: [
      { name: "客服工作台", path: "/customer-service-dashboard", icon: "LayoutDashboard", permission: "service:dashboard:read", permissionLabel: "客服工作台" },
      { name: "服务工单", path: "/service-tickets", icon: "FileText", permission: "service:ticket:read", permissionLabel: "服务工单" },
      { name: "服务记录", path: "/service-records", icon: "ClipboardCheck", permission: "service:record:read", permissionLabel: "服务记录" },
      { name: "客户沟通", path: "/customer-communications", icon: "MessageSquare", permission: "customer:communication:read", permissionLabel: "客户沟通" },
      { name: "满意度调查", path: "/customer-satisfaction", icon: "Star", permission: "customer:satisfaction:read", permissionLabel: "满意度调查" },
      { name: "服务分析", path: "/service-analytics", icon: "BarChart3", permission: "service:analytics:read", permissionLabel: "服务分析" },
      { name: "服务知识库", path: "/service-knowledge-base", icon: "BookOpen", permission: "service:knowledge:read", permissionLabel: "服务知识库" },
      { name: "验收管理", path: "/acceptance", icon: "ClipboardList", permission: "acceptance:read", permissionLabel: "验收管理" },
      { name: "验收订单", path: "/acceptance-orders", icon: "ClipboardCheck", permission: "acceptance:order:read", permissionLabel: "验收订单" },
      { name: "验收模板", path: "/acceptance-templates", icon: "FileText", permission: "acceptance:template:read", permissionLabel: "验收模板" },
      { name: "安装调试", path: "/installation-dispatch", icon: "Settings", permission: "installation:read", permissionLabel: "安装调试" }
    ]
  },
  // 12. 财务管理
  {
    label: "财务管理",
    items: [
      { name: "财务工作台", path: "/finance-manager-dashboard", icon: "LayoutDashboard", permission: "finance:dashboard:read", permissionLabel: "财务工作台" },
      { name: "财务成本", path: "/cost-quotes/financial-costs", icon: "DollarSign", permission: "finance:cost:read", permissionLabel: "财务成本" },
      { name: "成本核算", path: "/costs", icon: "Calculator", permission: "cost:accounting:read", permissionLabel: "成本核算" },
      { name: "付款审批", path: "/payment-approval", icon: "ClipboardCheck", permission: "payment:approve", permissionLabel: "付款审批" },
      { name: "项目结算", path: "/settlement", icon: "FileText", permission: "settlement:read", permissionLabel: "项目结算" },
      { name: "财务报表", path: "/financial-reports", icon: "BarChart3", permission: "finance:report:read", permissionLabel: "财务报表" }
    ],
    roles: ["finance", "accounting", "财务", "会计", "admin", "super_admin"]
  },
  // 13. HR/绩效管理
  {
    label: "HR/绩效管理",
    items: [
      { name: "HR经理工作台", path: "/hr-manager-dashboard", icon: "LayoutDashboard", permission: "hr:dashboard:read", permissionLabel: "HR工作台" },
      { name: "行政经理工作台", path: "/administrative-dashboard", icon: "Award", permission: "admin:dashboard:read", permissionLabel: "行政工作台" },
      { name: "绩效管理", path: "/performance", icon: "TrendingUp", permission: "performance:manage", permissionLabel: "绩效管理" },
      { name: "绩效排名", path: "/performance/ranking", icon: "Award", permission: "performance:ranking:read", permissionLabel: "绩效排名" },
      { name: "绩效指标", path: "/performance/indicators", icon: "Target", permission: "performance:indicator:read", permissionLabel: "绩效指标" },
      { name: "绩效结果", path: "/performance/results", icon: "BarChart3", permission: "performance:result:read", permissionLabel: "绩效结果" },
      { name: "资质管理", path: "/qualifications", icon: "Award", permission: "qualification:read", permissionLabel: "资质管理" },
      { name: "评价任务", path: "/evaluation-tasks", icon: "ListTodo", permission: "evaluation:task:read", permissionLabel: "评价任务" },
      { name: "评价权重配置", path: "/evaluation-weight-config", icon: "Settings", permission: "evaluation:config:manage", permissionLabel: "评价配置" }
    ]
  },
  // 14. AI人员匹配
  {
    label: "AI人员匹配",
    items: [
      { name: "标签管理", path: "/staff-matching/tags", icon: "Layers", permission: "staff:tag:manage", permissionLabel: "标签管理" },
      { name: "员工档案", path: "/staff-matching/profiles", icon: "Users", permission: "staff:profile:read", permissionLabel: "员工档案" },
      { name: "人员需求", path: "/staff-matching/staffing-needs", icon: "Target", permission: "staff:need:read", permissionLabel: "人员需求" },
      { name: "AI智能匹配", path: "/staff-matching/matching", icon: "Sparkles", permission: "staff:match:read", permissionLabel: "AI匹配" }
    ]
  },
  // 15. 个人中心
  {
    label: "个人中心",
    items: [
      { name: "通知中心", path: "/notifications", icon: "Bell" },
      { name: "工时填报", path: "/timesheet", icon: "Clock" },
      { name: "工时仪表板", path: "/timesheet/dashboard", icon: "Gauge", permission: "timesheet:dashboard:read", permissionLabel: "工时仪表板" },
      { name: "工时批量操作", path: "/timesheet/batch", icon: "ListTodo", permission: "timesheet:batch:manage", permissionLabel: "工时批量" },
      { name: "工作日志", path: "/work-log", icon: "ClipboardList" },
      { name: "月度总结", path: "/personal/monthly-summary", icon: "Calendar" },
      { name: "我的绩效", path: "/personal/my-performance", icon: "TrendingUp" },
      { name: "我的奖金", path: "/personal/my-bonus", icon: "DollarSign" },
      { name: "企业文化墙", path: "/culture-wall", icon: "Heart" },
      { name: "个人设置", path: "/settings", icon: "Settings" }
    ]
  },
  // 16. 系统管理
  {
    label: "系统管理",
    items: [
      { name: "用户管理", path: "/user-management", icon: "Users", permission: "system:user:manage", permissionLabel: "用户管理" },
      { name: "角色管理", path: "/role-management", icon: "Shield", permission: "system:role:manage", permissionLabel: "角色管理" },
      { name: "权限管理", path: "/permission-management", icon: "Key", permission: "system:permission:manage", permissionLabel: "权限管理" },
      { name: "项目角色", path: "/project-role-types", icon: "UserCog", permission: "system:projectrole:manage", permissionLabel: "项目角色管理" },
      { name: "部门管理", path: "/department-management", icon: "Building2", permission: "system:department:manage", permissionLabel: "部门管理" },
      { name: "组织管理", path: "/organization-management", icon: "Building2", permission: "system:org:manage", permissionLabel: "组织管理" },
      { name: "岗位管理", path: "/position-management", icon: "UserCog", permission: "system:position:manage", permissionLabel: "岗位管理" },
      { name: "人事管理", path: "/hr-management", icon: "Users", permission: "system:hr:manage", permissionLabel: "人事管理" },
      { name: "小时费率", path: "/hourly-rates", icon: "DollarSign", permission: "system:rate:manage", permissionLabel: "费率管理" },
      { name: "问题模板", path: "/issue-templates", icon: "FileText", permission: "system:template:manage", permissionLabel: "问题模板管理" },
      { name: "异常管理", path: "/exceptions", icon: "AlertCircle", permission: "system:exception:manage", permissionLabel: "异常管理" },
      { name: "预警规则", path: "/alert-rules", icon: "AlertTriangle", permission: "alert:rule:manage", permissionLabel: "预警规则" },
      { name: "预警统计", path: "/alert-statistics", icon: "BarChart3", permission: "alert:statistics:read", permissionLabel: "预警统计" },
      { name: "预警订阅", path: "/alert-subscription", icon: "Bell", permission: "alert:subscription:manage", permissionLabel: "预警订阅" },
      { name: "调度器监控", path: "/scheduler-monitoring", icon: "Activity", permission: "system:scheduler:read", permissionLabel: "调度器监控" },
      { name: "定时配置", path: "/scheduler-config", icon: "Cog", permission: "system:scheduler:manage", permissionLabel: "定时配置" },
      { name: "审计日志", path: "/audit-logs", icon: "FileText", permission: "system:audit:read", permissionLabel: "审计日志" },
      { name: "数据导入导出", path: "/data-import-export", icon: "Archive", permission: "system:data:manage", permissionLabel: "数据导入导出" },
      { name: "客户管理", path: "/customer-management", icon: "Building2", permission: "system:customer:manage", permissionLabel: "客户数据管理" },
      { name: "供应商管理", path: "/supplier-management-data", icon: "Truck", permission: "system:supplier:manage", permissionLabel: "供应商数据管理" }
    ],
    roles: ["admin", "super_admin"]
  }
];
