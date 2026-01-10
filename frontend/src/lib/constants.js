/**
 * 项目相关常量
 */

/**
 * 项目阶段配置
 */
export const PROJECT_STAGES = [
  { id: 'S1', name: '需求进入', color: 'bg-blue-500', textColor: 'text-blue-500' },
  { id: 'S2', name: '方案设计', color: 'bg-purple-500', textColor: 'text-purple-500' },
  { id: 'S3', name: '采购备料', color: 'bg-amber-500', textColor: 'text-amber-500' },
  { id: 'S4', name: '加工制造', color: 'bg-orange-500', textColor: 'text-orange-500' },
  { id: 'S5', name: '装配调试', color: 'bg-cyan-500', textColor: 'text-cyan-500' },
  { id: 'S6', name: '出厂验收', color: 'bg-indigo-500', textColor: 'text-indigo-500' },
  { id: 'S7', name: '包装发运', color: 'bg-pink-500', textColor: 'text-pink-500' },
  { id: 'S8', name: '现场安装', color: 'bg-teal-500', textColor: 'text-teal-500' },
  { id: 'S9', name: '质保结项', color: 'bg-emerald-500', textColor: 'text-emerald-500' },
]

/**
 * 项目状态配置
 */
export const PROJECT_STATUS = {
  ACTIVE: { label: '进行中', color: 'bg-blue-500', textColor: 'text-blue-500' },
  PAUSED: { label: '暂停', color: 'bg-amber-500', textColor: 'text-amber-500' },
  COMPLETED: { label: '已完成', color: 'bg-emerald-500', textColor: 'text-emerald-500' },
  CANCELLED: { label: '已取消', color: 'bg-red-500', textColor: 'text-red-500' },
}

/**
 * 健康度配置
 */
export const HEALTH_CONFIG = {
  H1: {
    id: 'H1',
    label: '正常',
    color: 'bg-emerald-500',
    textColor: 'text-emerald-500',
    borderColor: 'border-emerald-500',
    bgLight: 'bg-emerald-500/10',
  },
  H2: {
    id: 'H2',
    label: '有风险',
    color: 'bg-amber-500',
    textColor: 'text-amber-500',
    borderColor: 'border-amber-500',
    bgLight: 'bg-amber-500/10',
  },
  H3: {
    id: 'H3',
    label: '阻塞',
    color: 'bg-red-500',
    textColor: 'text-red-500',
    borderColor: 'border-red-500',
    bgLight: 'bg-red-500/10',
  },
  H4: {
    id: 'H4',
    label: '已完结',
    color: 'bg-slate-500',
    textColor: 'text-slate-500',
    borderColor: 'border-slate-500',
    bgLight: 'bg-slate-500/10',
  },
}

/**
 * 获取健康度配置
 * @param {string} health - 健康度代码 (H1, H2, H3, H4)
 * @returns {Object} 健康度配置对象
 */
export function getHealthConfig(health) {
  return HEALTH_CONFIG[health] || HEALTH_CONFIG.H1
}

/**
 * 优先级配置
 */
export const PRIORITY_CONFIG = {
  URGENT: { label: '紧急', color: 'bg-red-500', textColor: 'text-red-500' },
  HIGH: { label: '高', color: 'bg-orange-500', textColor: 'text-orange-500' },
  MEDIUM: { label: '中', color: 'bg-amber-500', textColor: 'text-amber-500' },
  LOW: { label: '低', color: 'bg-blue-500', textColor: 'text-blue-500' },
}

/**
 * 任务状态配置
 */
export const TASK_STATUS = {
  PENDING: { label: '待开始', color: 'bg-slate-500' },
  IN_PROGRESS: { label: '进行中', color: 'bg-blue-500' },
  COMPLETED: { label: '已完成', color: 'bg-emerald-500' },
  BLOCKED: { label: '阻塞', color: 'bg-red-500' },
}

/**
 * 物料类型配置
 */
export const MATERIAL_TYPES = {
  STANDARD: { label: '标准件', color: 'bg-blue-500' },
  MECHANICAL: { label: '机械件', color: 'bg-purple-500' },
  ELECTRICAL: { label: '电气件', color: 'bg-amber-500' },
  PNEUMATIC: { label: '气动件', color: 'bg-cyan-500' },
  OTHER: { label: '其他', color: 'bg-slate-500' },
}

/**
 * 审批状态配置
 */
export const APPROVAL_STATUS = {
  PENDING: { label: '待审批', color: 'bg-amber-500' },
  APPROVED: { label: '已通过', color: 'bg-emerald-500' },
  REJECTED: { label: '已驳回', color: 'bg-red-500' },
}
