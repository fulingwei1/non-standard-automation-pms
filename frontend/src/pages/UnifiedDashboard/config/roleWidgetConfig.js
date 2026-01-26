/**
 * 角色组件配置 (Role Widget Config)
 *
 * 统一使用数据库 roles.role_code 作为键
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
  // ============================================
  // 系统角色 (Level 0)
  // ============================================
  'ADMIN': {
    label: '系统管理员',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'admin', metrics: ['users', 'roles', 'logins', 'errors'] } },
      { id: 'system-health' },
      { id: 'user-stats' },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  // ============================================
  // 管理层角色 (Level 1)
  // ============================================
  'GM': {
    label: '总经理',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'executive', metrics: ['revenue', 'profit', 'projects', 'employees'] } },
      { id: 'revenue-chart', props: { view: 'executive' } },
      { id: 'trend-chart', props: { type: 'company-kpi' } },
      { id: 'project-progress', props: { view: 'executive' } },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  'CFO': {
    label: '财务总监',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'cfo', metrics: ['revenue', 'costs', 'profit', 'cash-flow', 'receivables'] } },
      { id: 'trend-chart', props: { type: 'financial' } },
      { id: 'approval-pending' },
      { id: 'task-list', props: { filter: 'finance' } },
      { id: 'notification-panel' },
    ],
  },

  'CTO': {
    label: '技术总监',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'cto', metrics: ['projects', 'engineers', 'deliverables', 'issues'] } },
      { id: 'project-progress', props: { view: 'engineering' } },
      { id: 'trend-chart', props: { type: 'engineering-kpi' } },
      { id: 'task-list', props: { filter: 'engineering' } },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  'SALES_DIR': {
    label: '销售总监',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'sales-director', metrics: ['total-revenue', 'ytd-growth', 'forecast', 'headcount'] } },
      { id: 'revenue-chart', props: { view: 'overview' } },
      { id: 'sales-funnel', props: { view: 'department' } },
      { id: 'opportunity-board', props: { view: 'high-value' } },
      { id: 'approval-pending' },
      { id: 'trend-chart', props: { type: 'revenue' } },
    ],
  },

  // ============================================
  // 主管级角色 (Level 2)
  // ============================================
  'PM': {
    label: '项目经理',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'pm', metrics: ['my-projects', 'tasks', 'issues', 'timeline'] } },
      { id: 'project-progress', props: { view: 'my-projects' } },
      { id: 'task-list', props: { filter: 'project' } },
      { id: 'timesheet-summary' },
      { id: 'notification-panel' },
    ],
  },

  'PMC': {
    label: '计划管理',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'pmc', metrics: ['my-projects', 'on-track', 'issues', 'milestones'] } },
      { id: 'project-progress', props: { view: 'my-projects' } },
      { id: 'kit-status' },
      { id: 'task-list', props: { filter: 'project' } },
      { id: 'ecn-list', props: { limit: 5 } },
      { id: 'notification-panel' },
    ],
  },

  'QA_MGR': {
    label: '质量主管',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'qa-manager', metrics: ['acceptances', 'issues', 'resolution-rate', 'customer-satisfaction'] } },
      { id: 'trend-chart', props: { type: 'quality-metrics' } },
      { id: 'task-list', props: { filter: 'quality' } },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  'PU_MGR': {
    label: '采购主管',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'procurement-manager', metrics: ['total-orders', 'budget', 'suppliers', 'lead-time'] } },
      { id: 'approval-pending' },
      { id: 'trend-chart', props: { type: 'procurement-spend' } },
      { id: 'kit-status', props: { view: 'overview' } },
      { id: 'notification-panel' },
    ],
  },

  // ============================================
  // 专员级角色 (Level 3)
  // ============================================
  // 工程技术
  'ME': {
    label: '机械工程师',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'engineer', metrics: ['tasks', 'hours-logged', 'designs', 'reviews'] } },
      { id: 'task-list', props: { filter: 'mechanical' } },
      { id: 'project-progress', props: { view: 'my-tasks' } },
      { id: 'timesheet-summary' },
      { id: 'ecn-list', props: { filter: 'mechanical' } },
    ],
  },

  'EE': {
    label: '电气工程师',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'engineer', metrics: ['tasks', 'hours-logged', 'designs', 'reviews'] } },
      { id: 'task-list', props: { filter: 'electrical' } },
      { id: 'project-progress', props: { view: 'my-tasks' } },
      { id: 'timesheet-summary' },
      { id: 'ecn-list', props: { filter: 'electrical' } },
    ],
  },

  'SW': {
    label: '软件工程师',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'engineer', metrics: ['tasks', 'hours-logged', 'commits', 'reviews'] } },
      { id: 'task-list', props: { filter: 'software' } },
      { id: 'project-progress', props: { view: 'my-tasks' } },
      { id: 'timesheet-summary' },
    ],
  },

  'DEBUG': {
    label: '调试工程师',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'engineer', metrics: ['tasks', 'hours-logged', 'debug-sessions', 'issues-resolved'] } },
      { id: 'task-list', props: { filter: 'debug' } },
      { id: 'project-progress', props: { view: 'my-tasks' } },
      { id: 'timesheet-summary' },
      { id: 'ecn-list', props: { filter: 'debug' } },
    ],
  },

  // 质量
  'QA': {
    label: '质量工程师',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'qa', metrics: ['inspections', 'issues-found', 'approvals', 'rejection-rate'] } },
      { id: 'task-list', props: { filter: 'quality' } },
      { id: 'project-progress', props: { view: 'my-tasks' } },
      { id: 'ecn-list', props: { filter: 'quality' } },
      { id: 'notification-panel' },
    ],
  },

  // 采购
  'PU': {
    label: '采购专员',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'buyer', metrics: ['orders', 'arrivals', 'issues', 'urgent'] } },
      { id: 'task-list', props: { filter: 'buyer' } },
      { id: 'recent-items', props: { type: 'purchase-orders' } },
      { id: 'notification-panel' },
    ],
  },

  // 财务
  'FI': {
    label: '财务专员',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'finance', metrics: ['invoices', 'payments', 'receivables', 'payables'] } },
      { id: 'task-list', props: { filter: 'finance' } },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  // 销售
  'SA': {
    label: '销售专员',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'sales', metrics: ['leads', 'opportunities', 'contracts', 'revenue'] } },
      { id: 'sales-funnel' },
      { id: 'leads-list', props: { limit: 10 } },
      { id: 'task-list', props: { filter: 'sales' } },
      { id: 'customer-list', props: { limit: 5 } },
      { id: 'notification-panel' },
    ],
  },

  // 生产
  'ASSEMBLER': {
    label: '装配技师',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'assembler', metrics: ['my-tasks', 'completed', 'in-progress', 'quality'] } },
      { id: 'work-order-list', props: { filter: 'my-orders' } },
      { id: 'task-list', props: { filter: 'assembly' } },
      { id: 'notification-panel' },
    ],
  },

  // ============================================
  // 外部角色 (Level 4)
  // ============================================
  'CUSTOMER': {
    label: '客户',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'customer', metrics: ['my-projects', 'progress', 'deliveries', 'payments'] } },
      { id: 'project-progress', props: { view: 'my-projects' } },
      { id: 'notification-panel' },
    ],
  },

  'SUPPLIER': {
    label: '供应商',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'supplier', metrics: ['orders', 'deliveries', 'quality', 'on-time'] } },
      { id: 'recent-items', props: { type: 'purchase-orders' } },
      { id: 'notification-panel' },
    ],
  },

  // ============================================
  // 扩展角色 (2026-01-22 新增)
  // ============================================
  // 高管扩展
  'CHAIRMAN': {
    label: '董事长',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'chairman', metrics: ['annual-revenue', 'growth', 'market-share', 'roi'] } },
      { id: 'revenue-chart', props: { view: 'strategic' } },
      { id: 'trend-chart', props: { type: 'strategic-kpi' } },
      { id: 'notification-panel', props: { filter: 'critical' } },
    ],
  },

  'VICE_CHAIRMAN': {
    label: '副总经理',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'executive', metrics: ['revenue', 'profit', 'projects', 'employees'] } },
      { id: 'revenue-chart', props: { view: 'executive' } },
      { id: 'trend-chart', props: { type: 'company-kpi' } },
      { id: 'project-progress', props: { view: 'department' } },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  'DONGMI': {
    label: '董秘',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'executive', metrics: ['revenue', 'profit', 'projects', 'employees'] } },
      { id: 'revenue-chart', props: { view: 'executive' } },
      { id: 'trend-chart', props: { type: 'company-kpi' } },
      { id: 'project-progress', props: { view: 'executive' } },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  // 售前
  'PRESALES_MGR': {
    label: '售前经理',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'presales-manager', metrics: ['proposals', 'win-rate', 'team-workload', 'active-projects'] } },
      { id: 'trend-chart', props: { type: 'presales-metrics' } },
      { id: 'task-list', props: { filter: 'presales-team' } },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  'PRESALES': {
    label: '售前工程师',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
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
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'business', metrics: ['contracts', 'orders', 'deliveries', 'collections'] } },
      { id: 'task-list', props: { filter: 'business' } },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  // 客服
  'CUSTOMER_SERVICE_MGR': {
    label: '客服经理',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'cs-manager', metrics: ['total-tickets', 'sla', 'csat', 'team-load'] } },
      { id: 'trend-chart', props: { type: 'service-metrics' } },
      { id: 'task-list', props: { filter: 'service-team' } },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  'CUSTOMER_SERVICE': {
    label: '客服工程师',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'customer-service', metrics: ['tickets', 'open', 'resolved', 'satisfaction'] } },
      { id: 'task-list', props: { filter: 'service' } },
      { id: 'recent-items', props: { type: 'tickets' } },
      { id: 'notification-panel' },
    ],
  },

  // HR
  'HR_MGR': {
    label: 'HR经理',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'hr-manager', metrics: ['headcount', 'turnover', 'hiring', 'training'] } },
      { id: 'trend-chart', props: { type: 'hr-metrics' } },
      { id: 'approval-pending' },
      { id: 'task-list', props: { filter: 'hr-team' } },
      { id: 'notification-panel' },
    ],
  },

  'HR': {
    label: 'HR专员',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'hr', metrics: ['employees', 'new-hires', 'attendance', 'leave-requests'] } },
      { id: 'task-list', props: { filter: 'hr' } },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
  },

  // 仓储
  'WAREHOUSE_MGR': {
    label: '仓储经理',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'warehouse-manager', metrics: ['inventory-value', 'turnover', 'accuracy', 'space-utilization'] } },
      { id: 'trend-chart', props: { type: 'inventory-metrics' } },
      { id: 'approval-pending' },
      { id: 'task-list', props: { filter: 'warehouse-team' } },
      { id: 'notification-panel' },
    ],
  },

  'WAREHOUSE': {
    label: '仓储管理员',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'warehouse', metrics: ['pending-tasks', 'inbound', 'outbound', 'count'] } },
      { id: 'task-list', props: { filter: 'warehouse' } },
      { id: 'inventory-alert' },
      { id: 'notification-panel' },
    ],
  },

  // 生产管理扩展
  'MANUFACTURING_DIR': {
    label: '制造总监',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'manufacturing', metrics: ['total-output', 'oee', 'quality-rate', 'on-time-delivery'] } },
      { id: 'trend-chart', props: { type: 'manufacturing-kpi' } },
      { id: 'production-board', props: { view: 'executive' } },
      { id: 'kit-status', props: { view: 'summary' } },
      { id: 'approval-pending' },
    ],
  },

  'PRODUCTION_MGR': {
    label: '生产经理',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card', props: { type: 'production-manager', metrics: ['capacity', 'efficiency', 'quality', 'delivery'] } },
      { id: 'production-board', props: { view: 'overview' } },
      { id: 'trend-chart', props: { type: 'production-output' } },
      { id: 'kit-status', props: { view: 'critical' } },
      { id: 'work-order-list', props: { filter: 'priority' } },
      { id: 'approval-pending' },
    ],
  },

  // ============================================
  // 默认配置
  // ============================================
  'DEFAULT': {
    label: '默认',
    layout: '2-column',
    widgets: [
      { id: 'welcome-card', size: 'full' },
      { id: 'culture-wall', size: 'full' },
      { id: 'stats-card' },
      { id: 'task-list' },
      { id: 'notification-panel' },
      { id: 'quick-actions' },
    ],
  },
};

/**
 * 获取角色配置
 * @param {string} roleCode - 数据库角色码（如 'GM', 'PM', 'ME'）
 * @returns {Object} 角色配置
 */
export function getRoleConfig(roleCode) {
  if (!roleCode) return roleWidgetConfig['DEFAULT'];

  const upperCode = roleCode.toUpperCase();

  // 精确匹配
  if (roleWidgetConfig[upperCode]) {
    return roleWidgetConfig[upperCode];
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

/**
 * 获取角色标签
 * @param {string} roleCode - 数据库角色码
 * @returns {string} 角色显示名称
 */
export function getRoleLabel(roleCode) {
  const config = getRoleConfig(roleCode);
  return config?.label || '未知角色';
}

export default roleWidgetConfig;
