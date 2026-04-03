/**
 * 组件注册表 (Widget Registry)
 *
 * 定义所有可用的工作台组件，通过配置驱动渲染
 * 组件按类别分组：通用、销售、工程、生产、管理
 */

import { lazy } from 'react';

// 使用 lazy 加载组件以提升性能
const WelcomeCard = lazy(() => import('../widgets/WelcomeCard'));
const CultureWallWidget = lazy(() => import('../widgets/CultureWallWidget'));
const StatsCard = lazy(() => import('../widgets/StatsCard'));
const TaskList = lazy(() => import('../widgets/TaskList'));
const NotificationPanel = lazy(() => import('../widgets/NotificationPanel'));
const QuickActions = lazy(() => import('../widgets/QuickActions'));
const RecentItems = lazy(() => import('../widgets/RecentItems'));
const TrendChart = lazy(() => import('../widgets/TrendChart'));
const ApprovalPending = lazy(() => import('../widgets/ApprovalPending'));

// 销售组件
const SalesFunnel = lazy(() => import('../widgets/sales/SalesFunnel'));
const LeadsList = lazy(() => import('../widgets/sales/LeadsList'));
const OpportunityBoard = lazy(() => import('../widgets/sales/OpportunityBoard'));
const RevenueChart = lazy(() => import('../widgets/sales/RevenueChart'));
const CustomerList = lazy(() => import('../widgets/sales/CustomerList'));

// 工程组件
const ProjectProgress = lazy(() => import('../widgets/engineer/ProjectProgress'));
const TimesheetSummary = lazy(() => import('../widgets/engineer/TimesheetSummary'));
const EcnList = lazy(() => import('../widgets/engineer/EcnList'));

// 生产组件
const ProductionBoard = lazy(() => import('../widgets/production/ProductionBoard'));
const KitStatus = lazy(() => import('../widgets/production/KitStatus'));
const WorkOrderList = lazy(() => import('../widgets/production/WorkOrderList'));

// 管理组件
const SystemHealth = lazy(() => import('../widgets/admin/SystemHealth'));
const UserStats = lazy(() => import('../widgets/admin/UserStats'));

// PM 视图组件
const PmProjectHealth = lazy(() => import('../widgets/pm/PmProjectHealth'));
const PmMilestoneReminder = lazy(() => import('../widgets/pm/PmMilestoneReminder'));
const PmRiskOverview = lazy(() => import('../widgets/pm/PmRiskOverview'));
const PmResourceConflict = lazy(() => import('../widgets/pm/PmResourceConflict'));

// 高管视图组件
const ExecPortfolioHealth = lazy(() => import('../widgets/executive/ExecPortfolioHealth'));
const ExecStrategicProjects = lazy(() => import('../widgets/executive/ExecStrategicProjects'));
const ExecMajorRisks = lazy(() => import('../widgets/executive/ExecMajorRisks'));
const ExecRoiAnalysis = lazy(() => import('../widgets/executive/ExecRoiAnalysis'));

// 部门负责人视图组件
const DeptProjectRanking = lazy(() => import('../widgets/dept-head/DeptProjectRanking'));
const DeptResourceLoad = lazy(() => import('../widgets/dept-head/DeptResourceLoad'));
const DeptRiskSummary = lazy(() => import('../widgets/dept-head/DeptRiskSummary'));
const DeptBudgetExecution = lazy(() => import('../widgets/dept-head/DeptBudgetExecution'));

// 成员视图组件
const MemberTaskList = lazy(() => import('../widgets/member/MemberTaskList'));
const MemberProjectProgress = lazy(() => import('../widgets/member/MemberProjectProgress'));
const MemberTimesheetTrend = lazy(() => import('../widgets/member/MemberTimesheetTrend'));
const MemberOverdueAlert = lazy(() => import('../widgets/member/MemberOverdueAlert'));

/**
 * 组件注册表
 *
 * 每个组件包含：
 * - component: 组件引用
 * - category: 所属类别（common/sales/engineer/production/admin）
 * - defaultSize: 默认尺寸（small/medium/large/full）
 * - description: 组件描述（中文）
 */
export const widgetRegistry = {
  // ============ 通用组件 ============
  'welcome-card': {
    component: WelcomeCard,
    category: 'common',
    defaultSize: 'full',
    description: '欢迎卡片（整合自工作中心）'
  },
  'culture-wall': {
    component: CultureWallWidget,
    category: 'common',
    defaultSize: 'full',
    description: '企业文化墙（高流量位置展示企业文化）'
  },
  'stats-card': {
    component: StatsCard,
    category: 'common',
    defaultSize: 'small',
    description: '统计卡片'
  },
  'task-list': {
    component: TaskList,
    category: 'common',
    defaultSize: 'medium',
    description: '待办任务列表'
  },
  'notification-panel': {
    component: NotificationPanel,
    category: 'common',
    defaultSize: 'medium',
    description: '通知/预警面板'
  },
  'quick-actions': {
    component: QuickActions,
    category: 'common',
    defaultSize: 'small',
    description: '快捷操作'
  },
  'recent-items': {
    component: RecentItems,
    category: 'common',
    defaultSize: 'medium',
    description: '最近访问'
  },
  'trend-chart': {
    component: TrendChart,
    category: 'common',
    defaultSize: 'large',
    description: '趋势图表'
  },
  'approval-pending': {
    component: ApprovalPending,
    category: 'common',
    defaultSize: 'medium',
    description: '待审批事项'
  },

  // ============ 销售组件 ============
  'sales-funnel': {
    component: SalesFunnel,
    category: 'sales',
    defaultSize: 'large',
    description: '销售漏斗'
  },
  'leads-list': {
    component: LeadsList,
    category: 'sales',
    defaultSize: 'medium',
    description: '线索列表'
  },
  'opportunity-board': {
    component: OpportunityBoard,
    category: 'sales',
    defaultSize: 'large',
    description: '商机看板'
  },
  'revenue-chart': {
    component: RevenueChart,
    category: 'sales',
    defaultSize: 'large',
    description: '营收图表'
  },
  'customer-list': {
    component: CustomerList,
    category: 'sales',
    defaultSize: 'medium',
    description: '客户列表'
  },

  // ============ 工程组件 ============
  'project-progress': {
    component: ProjectProgress,
    category: 'engineer',
    defaultSize: 'large',
    description: '项目进度'
  },
  'timesheet-summary': {
    component: TimesheetSummary,
    category: 'engineer',
    defaultSize: 'medium',
    description: '工时汇总'
  },
  'ecn-list': {
    component: EcnList,
    category: 'engineer',
    defaultSize: 'medium',
    description: 'ECN变更列表'
  },

  // ============ 生产组件 ============
  'production-board': {
    component: ProductionBoard,
    category: 'production',
    defaultSize: 'large',
    description: '生产看板'
  },
  'kit-status': {
    component: KitStatus,
    category: 'production',
    defaultSize: 'medium',
    description: '齐套状态'
  },
  'work-order-list': {
    component: WorkOrderList,
    category: 'production',
    defaultSize: 'medium',
    description: '工单列表'
  },

  // ============ 管理组件 ============
  'system-health': {
    component: SystemHealth,
    category: 'admin',
    defaultSize: 'medium',
    description: '系统健康'
  },
  'user-stats': {
    component: UserStats,
    category: 'admin',
    defaultSize: 'medium',
    description: '用户统计'
  },

  // ============ PM 视图组件 ============
  'pm-project-health': {
    component: PmProjectHealth,
    category: 'pm-view',
    defaultSize: 'large',
    description: '项目健康度一览'
  },
  'pm-milestone-reminder': {
    component: PmMilestoneReminder,
    category: 'pm-view',
    defaultSize: 'medium',
    description: '近期里程碑提醒'
  },
  'pm-risk-overview': {
    component: PmRiskOverview,
    category: 'pm-view',
    defaultSize: 'medium',
    description: '活跃风险TOP'
  },
  'pm-resource-conflict': {
    component: PmResourceConflict,
    category: 'pm-view',
    defaultSize: 'medium',
    description: '资源冲突告警'
  },

  // ============ 高管视图组件 ============
  'exec-portfolio-health': {
    component: ExecPortfolioHealth,
    category: 'executive-view',
    defaultSize: 'medium',
    description: '项目组合健康度'
  },
  'exec-strategic-projects': {
    component: ExecStrategicProjects,
    category: 'executive-view',
    defaultSize: 'large',
    description: '战略项目进度'
  },
  'exec-major-risks': {
    component: ExecMajorRisks,
    category: 'executive-view',
    defaultSize: 'medium',
    description: '重大风险/问题'
  },
  'exec-roi-analysis': {
    component: ExecRoiAnalysis,
    category: 'executive-view',
    defaultSize: 'large',
    description: '投资回报率分析'
  },

  // ============ 部门负责人视图组件 ============
  'dept-project-ranking': {
    component: DeptProjectRanking,
    category: 'dept-head-view',
    defaultSize: 'large',
    description: '部门项目绩效排行'
  },
  'dept-resource-load': {
    component: DeptResourceLoad,
    category: 'dept-head-view',
    defaultSize: 'medium',
    description: '部门资源负荷'
  },
  'dept-risk-summary': {
    component: DeptRiskSummary,
    category: 'dept-head-view',
    defaultSize: 'medium',
    description: '部门风险汇总'
  },
  'dept-budget-execution': {
    component: DeptBudgetExecution,
    category: 'dept-head-view',
    defaultSize: 'large',
    description: '预算执行率统计'
  },

  // ============ 成员视图组件 ============
  'member-task-list': {
    component: MemberTaskList,
    category: 'member-view',
    defaultSize: 'large',
    description: '我的任务'
  },
  'member-project-progress': {
    component: MemberProjectProgress,
    category: 'member-view',
    defaultSize: 'medium',
    description: '参与项目进度'
  },
  'member-timesheet-trend': {
    component: MemberTimesheetTrend,
    category: 'member-view',
    defaultSize: 'medium',
    description: '个人工时趋势'
  },
  'member-overdue-alert': {
    component: MemberOverdueAlert,
    category: 'member-view',
    defaultSize: 'medium',
    description: '逾期任务告警'
  },
};

/**
 * 获取组件
 * @param {string} widgetId - 组件ID
 * @returns {Object|null} 组件配置
 */
export function getWidget(widgetId) {
  return widgetRegistry[widgetId] || null;
}

/**
 * 按类别获取组件列表
 * @param {string} category - 类别
 * @returns {Array} 组件配置列表
 */
export function getWidgetsByCategory(category) {
  return Object.entries(widgetRegistry)
    .filter(([, config]) => config.category === category)
    .map(([id, config]) => ({ id, ...config }));
}

/**
 * 获取所有类别
 * @returns {string[]} 类别列表
 */
export function getAllCategories() {
  const categories = new Set(
    Object.values(widgetRegistry).map(config => config.category)
  );
  return Array.from(categories);
}

export default widgetRegistry;
