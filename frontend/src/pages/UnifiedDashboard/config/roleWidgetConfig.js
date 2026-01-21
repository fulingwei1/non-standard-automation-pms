/**
 * 角色组件配置 (Role Widget Config)
 *
 * 定义每个角色在工作台上看到的组件布局
 * 组件配置包含：id（对应 widgetRegistry）、props（自定义属性）、size（覆盖默认尺寸）
 */

/**
 * 角色工作台配置
 *
 * 每个角色配置包含：
 * - label: 角色显示名称
 * - widgets: 组件列表
 * - layout: 布局模式（1-column, 2-column, 3-column, dashboard）
 */
export const roleWidgetConfig = {
  // ============ 销售系统角色 ============
  'SALES': {
    label: '销售工程师',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'sales', metrics: ['leads', 'opportunities', 'contracts', 'revenue'] } },
      { id: 'sales-funnel' },
      { id: 'leads-list', props: { limit: 10 } },
      { id: 'task-list', props: { filter: 'sales' } },
      { id: 'customer-list', props: { limit: 5 } },
      { id: 'notification-panel' },
    ],
  },

  'SALES_MANAGER': {
    label: '销售经理',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'sales-manager', metrics: ['team-revenue', 'team-quota', 'pipeline', 'win-rate'] } },
      { id: 'revenue-chart' },
      { id: 'sales-funnel' },
      { id: 'opportunity-board' },
      { id: 'task-list', props: { filter: 'sales' } },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  'SALES_DIRECTOR': {
    label: '销售总监',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'sales-director', metrics: ['total-revenue', 'ytd-growth', 'forecast', 'headcount'] } },
      { id: 'revenue-chart', props: { view: 'overview' } },
      { id: 'sales-funnel', props: { view: 'department' } },
      { id: 'opportunity-board', props: { view: 'high-value' } },
      { id: 'approval-pending' },
      { id: 'trend-chart', props: { type: 'revenue' } },
    ],
  },

  'PRESALES': {
    label: '售前工程师',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'presales', metrics: ['proposals', 'win-rate', 'response-time', 'active-projects'] } },
      { id: 'task-list', props: { filter: 'presales' } },
      { id: 'project-progress', props: { filter: 'presales' } },
      { id: 'recent-items', props: { type: 'proposals' } },
      { id: 'notification-panel' },
    ],
  },

  'BUSINESS_SUPPORT': {
    label: '商务支持',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'business', metrics: ['contracts', 'orders', 'deliveries', 'collections'] } },
      { id: 'task-list', props: { filter: 'business' } },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  // ============ 项目管理角色 ============
  'PMO_DIR': {
    label: '项目管理部总监',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'pmo', metrics: ['active-projects', 'on-track', 'delayed', 'completed'] } },
      { id: 'project-progress', props: { view: 'overview' } },
      { id: 'trend-chart', props: { type: 'project-health' } },
      { id: 'task-list', props: { filter: 'pmo' } },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  'PMC': {
    label: '项目经理(PMC)',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'pmc', metrics: ['my-projects', 'on-track', 'issues', 'milestones'] } },
      { id: 'project-progress', props: { view: 'my-projects' } },
      { id: 'kit-status' },
      { id: 'task-list', props: { filter: 'project' } },
      { id: 'ecn-list', props: { limit: 5 } },
      { id: 'notification-panel' },
    ],
  },

  'PM': {
    label: '项目经理',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'pm', metrics: ['my-projects', 'tasks', 'issues', 'timeline'] } },
      { id: 'project-progress', props: { view: 'my-projects' } },
      { id: 'task-list', props: { filter: 'project' } },
      { id: 'timesheet-summary' },
      { id: 'notification-panel' },
    ],
  },

  // ============ 工程技术角色 ============
  'ENGINEER': {
    label: '工程师',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'engineer', metrics: ['tasks', 'hours-logged', 'ecn-pending', 'reviews'] } },
      { id: 'task-list', props: { filter: 'engineer' } },
      { id: 'project-progress', props: { view: 'my-tasks' } },
      { id: 'timesheet-summary' },
      { id: 'ecn-list', props: { limit: 5 } },
      { id: 'notification-panel' },
    ],
  },

  'ME_ENGINEER': {
    label: '机械工程师',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'engineer', metrics: ['tasks', 'hours-logged', 'designs', 'reviews'] } },
      { id: 'task-list', props: { filter: 'mechanical' } },
      { id: 'project-progress', props: { view: 'my-tasks' } },
      { id: 'timesheet-summary' },
      { id: 'ecn-list', props: { filter: 'mechanical' } },
    ],
  },

  'EE_ENGINEER': {
    label: '电气工程师',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'engineer', metrics: ['tasks', 'hours-logged', 'designs', 'reviews'] } },
      { id: 'task-list', props: { filter: 'electrical' } },
      { id: 'project-progress', props: { view: 'my-tasks' } },
      { id: 'timesheet-summary' },
      { id: 'ecn-list', props: { filter: 'electrical' } },
    ],
  },

  'SW_ENGINEER': {
    label: '软件工程师',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'engineer', metrics: ['tasks', 'hours-logged', 'commits', 'reviews'] } },
      { id: 'task-list', props: { filter: 'software' } },
      { id: 'project-progress', props: { view: 'my-tasks' } },
      { id: 'timesheet-summary' },
    ],
  },

  'TE_ENGINEER': {
    label: '测试工程师',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'engineer', metrics: ['tasks', 'hours-logged', 'tests', 'bugs'] } },
      { id: 'task-list', props: { filter: 'testing' } },
      { id: 'project-progress', props: { view: 'my-tasks' } },
      { id: 'timesheet-summary' },
    ],
  },

  // ============ 采购角色 ============
  'PROCUREMENT': {
    label: '采购工程师',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'procurement', metrics: ['orders', 'pending', 'overdue', 'savings'] } },
      { id: 'task-list', props: { filter: 'procurement' } },
      { id: 'kit-status' },
      { id: 'recent-items', props: { type: 'purchase-orders' } },
      { id: 'notification-panel' },
    ],
  },

  'PROCUREMENT_MANAGER': {
    label: '采购经理',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'procurement-manager', metrics: ['total-orders', 'budget', 'suppliers', 'lead-time'] } },
      { id: 'approval-pending' },
      { id: 'trend-chart', props: { type: 'procurement-spend' } },
      { id: 'kit-status', props: { view: 'overview' } },
      { id: 'notification-panel' },
    ],
  },

  'BUYER': {
    label: '采购员',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'buyer', metrics: ['orders', 'arrivals', 'issues', 'urgent'] } },
      { id: 'task-list', props: { filter: 'buyer' } },
      { id: 'recent-items', props: { type: 'purchase-orders' } },
      { id: 'notification-panel' },
    ],
  },

  // ============ 生产角色 ============
  'PRODUCTION': {
    label: '生产管理',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'production', metrics: ['work-orders', 'in-progress', 'completed', 'yield'] } },
      { id: 'production-board' },
      { id: 'kit-status' },
      { id: 'work-order-list' },
      { id: 'task-list', props: { filter: 'production' } },
    ],
  },

  'PRODUCTION_MANAGER': {
    label: '生产经理',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'production-manager', metrics: ['capacity', 'efficiency', 'quality', 'delivery'] } },
      { id: 'production-board', props: { view: 'overview' } },
      { id: 'trend-chart', props: { type: 'production-output' } },
      { id: 'kit-status', props: { view: 'critical' } },
      { id: 'work-order-list', props: { filter: 'priority' } },
      { id: 'approval-pending' },
    ],
  },

  'MANUFACTURING_DIR': {
    label: '制造总监',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'manufacturing', metrics: ['total-output', 'oee', 'quality-rate', 'on-time-delivery'] } },
      { id: 'trend-chart', props: { type: 'manufacturing-kpi' } },
      { id: 'production-board', props: { view: 'executive' } },
      { id: 'kit-status', props: { view: 'summary' } },
      { id: 'approval-pending' },
    ],
  },

  'ASSEMBLER': {
    label: '装配工',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'assembler', metrics: ['my-tasks', 'completed', 'in-progress', 'quality'] } },
      { id: 'work-order-list', props: { filter: 'my-orders' } },
      { id: 'task-list', props: { filter: 'assembly' } },
      { id: 'notification-panel' },
    ],
  },

  // ============ 客服角色 ============
  'CUSTOMER_SERVICE': {
    label: '客服工程师',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'customer-service', metrics: ['tickets', 'open', 'resolved', 'satisfaction'] } },
      { id: 'task-list', props: { filter: 'service' } },
      { id: 'recent-items', props: { type: 'tickets' } },
      { id: 'notification-panel' },
    ],
  },

  'CUSTOMER_SERVICE_MANAGER': {
    label: '客服经理',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'cs-manager', metrics: ['total-tickets', 'sla', 'csat', 'team-load'] } },
      { id: 'trend-chart', props: { type: 'service-metrics' } },
      { id: 'task-list', props: { filter: 'service-team' } },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  // ============ 财务角色 ============
  'FINANCE': {
    label: '财务专员',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'finance', metrics: ['invoices', 'payments', 'receivables', 'payables'] } },
      { id: 'task-list', props: { filter: 'finance' } },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  'FINANCE_MANAGER': {
    label: '财务经理',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'finance-manager', metrics: ['revenue', 'costs', 'profit', 'cash-flow'] } },
      { id: 'trend-chart', props: { type: 'financial' } },
      { id: 'approval-pending' },
      { id: 'task-list', props: { filter: 'finance' } },
      { id: 'notification-panel' },
    ],
  },

  // ============ HR角色 ============
  'HR': {
    label: 'HR专员',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'hr', metrics: ['employees', 'new-hires', 'attendance', 'leave-requests'] } },
      { id: 'task-list', props: { filter: 'hr' } },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  'HR_MANAGER': {
    label: 'HR经理',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'hr-manager', metrics: ['headcount', 'turnover', 'hiring', 'training'] } },
      { id: 'trend-chart', props: { type: 'hr-metrics' } },
      { id: 'approval-pending' },
      { id: 'task-list', props: { filter: 'hr-team' } },
      { id: 'notification-panel' },
    ],
  },

  // ============ 高管角色 ============
  'GM': {
    label: '总经理',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'executive', metrics: ['revenue', 'profit', 'projects', 'employees'] } },
      { id: 'revenue-chart', props: { view: 'executive' } },
      { id: 'trend-chart', props: { type: 'company-kpi' } },
      { id: 'project-progress', props: { view: 'executive' } },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  'CHAIRMAN': {
    label: '董事长',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'chairman', metrics: ['annual-revenue', 'growth', 'market-share', 'roi'] } },
      { id: 'revenue-chart', props: { view: 'strategic' } },
      { id: 'trend-chart', props: { type: 'strategic-kpi' } },
      { id: 'notification-panel', props: { filter: 'critical' } },
    ],
  },

  'VP': {
    label: '副总经理',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'vp', metrics: ['dept-revenue', 'dept-projects', 'dept-headcount', 'dept-kpi'] } },
      { id: 'trend-chart', props: { type: 'dept-kpi' } },
      { id: 'project-progress', props: { view: 'department' } },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  // ============ 管理员角色 ============
  'ADMIN': {
    label: '系统管理员',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'admin', metrics: ['users', 'roles', 'logins', 'errors'] } },
      { id: 'system-health' },
      { id: 'user-stats' },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  'SUPER_ADMIN': {
    label: '超级管理员',
    layout: '2-column',
    widgets: [
      { id: 'stats-card', props: { type: 'super-admin', metrics: ['users', 'roles', 'permissions', 'system-load'] } },
      { id: 'system-health' },
      { id: 'user-stats' },
      { id: 'trend-chart', props: { type: 'system-metrics' } },
      { id: 'notification-panel' },
    ],
  },

  // ============ 默认配置 ============
  'DEFAULT': {
    label: '默认',
    layout: '2-column',
    widgets: [
      { id: 'stats-card' },
      { id: 'task-list' },
      { id: 'notification-panel' },
      { id: 'quick-actions' },
    ],
  },
};

/**
 * 获取角色配置
 * @param {string} roleCode - 角色编码
 * @returns {Object} 角色配置
 */
export function getRoleConfig(roleCode) {
  // 先尝试精确匹配
  if (roleWidgetConfig[roleCode]) {
    return roleWidgetConfig[roleCode];
  }

  // 尝试大写匹配
  const upperCode = roleCode?.toUpperCase();
  if (roleWidgetConfig[upperCode]) {
    return roleWidgetConfig[upperCode];
  }

  // 尝试模糊匹配（处理 sales_engineer -> SALES）
  const baseRole = upperCode?.split('_')[0];
  if (roleWidgetConfig[baseRole]) {
    return roleWidgetConfig[baseRole];
  }

  // 返回默认配置
  return roleWidgetConfig['DEFAULT'];
}

/**
 * 获取所有角色标签
 * @returns {Array} 角色列表 [{ code, label }]
 */
export function getAllRoleLabels() {
  return Object.entries(roleWidgetConfig)
    .filter(([code]) => code !== 'DEFAULT')
    .map(([code, config]) => ({
      code,
      label: config.label,
    }));
}

export default roleWidgetConfig;
