// 项目阶段配置
export const PROJECT_STAGES = [
  { key: 'S1', name: '立项启动', shortName: '立项', roles: ['pm', 'sales', 'gm', 'admin'] },
  { key: 'S2', name: '方案设计', shortName: '方案', roles: ['pm', 'te', 'me_engineer', 'ee_engineer', 'admin'] },
  { key: 'S3', name: '结构设计', shortName: '结构', roles: ['me_leader', 'me_engineer', 'admin'] },
  { key: 'S4', name: '电气设计', shortName: '电气', roles: ['ee_leader', 'ee_engineer', 'admin'] },
  { key: 'S5', name: '采购制造', shortName: '采购', roles: ['buyer', 'pmc', 'warehouse', 'admin'] },
  { key: 'S6', name: '装配调试', shortName: '装配', roles: ['te_leader', 'te_engineer', 'assembler', 'admin'] },
  { key: 'S7', name: '验收交付', shortName: '验收', roles: ['pm', 'qa', 'sales', 'admin'] },
  { key: 'S8', name: '现场安装', shortName: '安装', roles: ['te_engineer', 'pm', 'admin'] },
  { key: 'S9', name: '质保结项', shortName: '结项', roles: ['pm', 'finance', 'admin'] },
]

// 健康度配置
export const HEALTH_CONFIG = {
  H1: { 
    key: 'H1',
    color: 'emerald', 
    label: '正常', 
    bgClass: 'bg-emerald-500/20', 
    borderClass: 'border-l-emerald-500',
    textClass: 'text-emerald-400',
    dotClass: 'bg-emerald-500',
  },
  H2: { 
    key: 'H2',
    color: 'amber', 
    label: '关注', 
    bgClass: 'bg-amber-500/20', 
    borderClass: 'border-l-amber-500',
    textClass: 'text-amber-400',
    dotClass: 'bg-amber-500',
  },
  H3: { 
    key: 'H3',
    color: 'red', 
    label: '预警', 
    bgClass: 'bg-red-500/20', 
    borderClass: 'border-l-red-500',
    textClass: 'text-red-400',
    dotClass: 'bg-red-500',
  },
  H4: { 
    key: 'H4',
    color: 'slate', 
    label: '已完结', 
    bgClass: 'bg-slate-500/20', 
    borderClass: 'border-l-slate-500',
    textClass: 'text-slate-400',
    dotClass: 'bg-slate-500',
  },
}

// 项目状态配置
export const PROJECT_STATUS = {
  pending: { label: '未启动', color: 'slate' },
  active: { label: '进行中', color: 'blue' },
  paused: { label: '已暂停', color: 'yellow' },
  completed: { label: '已完成', color: 'green' },
  cancelled: { label: '已取消', color: 'red' },
  archived: { label: '已归档', color: 'gray' },
}

// 角色配置
export const ROLES = {
  admin: { name: '系统管理员', scope: 'all' },
  gm: { name: '总经理', scope: 'all' },
  dept_manager: { name: '部门经理', scope: 'department' },
  pm: { name: '项目经理', scope: 'project' },
  te: { name: '技术负责人', scope: 'project' },
  me_leader: { name: '机械组长', scope: 'group' },
  ee_leader: { name: '电气组长', scope: 'group' },
  te_leader: { name: '测试组长', scope: 'group' },
  me_engineer: { name: '机械工程师', scope: 'self' },
  ee_engineer: { name: '电气工程师', scope: 'self' },
  sw_engineer: { name: '软件工程师', scope: 'self' },
  te_engineer: { name: '测试工程师', scope: 'self' },
  buyer: { name: '采购员', scope: 'procurement' },
  warehouse: { name: '仓库管理员', scope: 'warehouse' },
  assembler: { name: '装配技工', scope: 'self' },
  qa: { name: '品质工程师', scope: 'all' },
  pmc: { name: 'PMC计划员', scope: 'all' },
  sales: { name: '销售/商务', scope: 'customer' },
  finance: { name: '财务人员', scope: 'finance' },
  viewer: { name: '只读用户', scope: 'limited' },
}

// 获取阶段名称
export function getStageName(stageKey) {
  const stage = PROJECT_STAGES.find(s => s.key === stageKey)
  return stage ? stage.name : stageKey
}

// 获取健康度配置
export function getHealthConfig(healthKey) {
  return HEALTH_CONFIG[healthKey] || HEALTH_CONFIG.H1
}

// 获取状态配置
export function getStatusConfig(statusKey) {
  return PROJECT_STATUS[statusKey] || PROJECT_STATUS.pending
}

