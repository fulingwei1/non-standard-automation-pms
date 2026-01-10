/**
 * ECN配置常量 - 从ECNDetail.jsx安全提取
 */

export const statusConfigs = {
  DRAFT: { label: '草稿', color: 'bg-slate-500' },
  SUBMITTED: { label: '已提交', color: 'bg-blue-500' },
  EVALUATING: { label: '评估中', color: 'bg-amber-500' },
  EVALUATED: { label: '评估完成', color: 'bg-amber-600' },
  PENDING_APPROVAL: { label: '待审批', color: 'bg-purple-500' },
  APPROVED: { label: '已批准', color: 'bg-emerald-500' },
  REJECTED: { label: '已驳回', color: 'bg-red-500' },
  EXECUTING: { label: '执行中', color: 'bg-violet-500' },
  PENDING_VERIFY: { label: '待验证', color: 'bg-indigo-500' },
  COMPLETED: { label: '已完成', color: 'bg-green-500' },
  CLOSED: { label: '已关闭', color: 'bg-gray-500' },
  CANCELLED: { label: '已取消', color: 'bg-gray-500' },
}

export const typeConfigs = {
  // 客户相关（3种）
  CUSTOMER_REQUIREMENT: { label: '客户需求变更', color: 'bg-blue-500' },
  CUSTOMER_SPEC: { label: '客户规格调整', color: 'bg-blue-400' },
  CUSTOMER_FEEDBACK: { label: '客户现场反馈', color: 'bg-blue-600' },

  // 设计变更（5种）
  MECHANICAL_STRUCTURE: { label: '机械结构变更', color: 'bg-cyan-500' },
  ELECTRICAL_SCHEME: { label: '电气方案变更', color: 'bg-cyan-400' },
  SOFTWARE_FUNCTION: { label: '软件功能变更', color: 'bg-cyan-600' },
  TECH_OPTIMIZATION: { label: '技术方案优化', color: 'bg-teal-500' },
  DESIGN_FIX: { label: '设计缺陷修复', color: 'bg-teal-600' },

  // 测试相关（4种）
  TEST_STANDARD: { label: '测试标准变更', color: 'bg-purple-500' },
  TEST_FIXTURE: { label: '测试工装变更', color: 'bg-purple-400' },
  CALIBRATION_SCHEME: { label: '校准方案变更', color: 'bg-purple-600' },
  TEST_PROGRAM: { label: '测试程序变更', color: 'bg-violet-500' },

  // 生产制造（4种）
  PROCESS_IMPROVEMENT: { label: '工艺改进', color: 'bg-orange-500' },
  MATERIAL_SUBSTITUTE: { label: '物料替代', color: 'bg-orange-400' },
  SUPPLIER_CHANGE: { label: '供应商变更', color: 'bg-orange-600' },
  COST_OPTIMIZATION: { label: '成本优化', color: 'bg-amber-500' },

  // 质量安全（3种）
  QUALITY_ISSUE: { label: '质量问题整改', color: 'bg-red-500' },
  SAFETY_COMPLIANCE: { label: '安全合规变更', color: 'bg-red-600' },
  RELIABILITY_IMPROVEMENT: { label: '可靠性改进', color: 'bg-rose-500' },

  // 项目管理（3种）
  SCHEDULE_ADJUSTMENT: { label: '进度调整', color: 'bg-green-500' },
  DOCUMENT_UPDATE: { label: '文档更新', color: 'bg-green-400' },
  DRAWING_CHANGE: { label: '图纸变更', color: 'bg-emerald-500' },

  // 兼容旧版本
  DESIGN: { label: '设计变更', color: 'bg-blue-500' },
  MATERIAL: { label: '物料变更', color: 'bg-amber-500' },
  PROCESS: { label: '工艺变更', color: 'bg-purple-500' },
  SPECIFICATION: { label: '规格变更', color: 'bg-green-500' },
  SCHEDULE: { label: '计划变更', color: 'bg-orange-500' },
  OTHER: { label: '其他', color: 'bg-slate-500' },
}

export const priorityConfigs = {
  URGENT: { label: '紧急', color: 'bg-red-500' },
  HIGH: { label: '高', color: 'bg-orange-500' },
  MEDIUM: { label: '中', color: 'bg-amber-500' },
  LOW: { label: '低', color: 'bg-blue-500' },
}

export const evalResultConfigs = {
  APPROVED: { label: '通过', color: 'bg-green-500' },
  CONDITIONAL: { label: '有条件通过', color: 'bg-yellow-500' },
  REJECTED: { label: '不通过', color: 'bg-red-500' },
}

export const taskStatusConfigs = {
  PENDING: { label: '待开始', color: 'bg-slate-500' },
  IN_PROGRESS: { label: '进行中', color: 'bg-blue-500' },
  COMPLETED: { label: '已完成', color: 'bg-green-500' },
}

export const rootCauseCategories = [
  { value: 'DESIGN_DEFECT', label: '设计缺陷' },
  { value: 'PROCESS_ISSUE', label: '工艺问题' },
  { value: 'MATERIAL_ISSUE', label: '物料问题' },
  { value: 'HUMAN_ERROR', label: '人为失误' },
  { value: 'EQUIPMENT_ISSUE', label: '设备问题' },
  { value: 'ENVIRONMENTAL', label: '环境因素' },
  { value: 'COMMUNICATION', label: '沟通问题' },
  { value: 'REQUIREMENT_CHANGE', label: '需求变更' },
  { value: 'OTHER', label: '其他' },
]
