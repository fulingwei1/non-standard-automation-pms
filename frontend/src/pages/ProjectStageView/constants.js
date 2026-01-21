/**
 * 项目阶段视图常量定义
 */

// 阶段状态配置
export const STAGE_STATUS = {
  PENDING: {
    value: "PENDING",
    label: "待开始",
    color: "#6B7280", // gray-500
    bgColor: "bg-gray-500/20",
    textColor: "text-gray-400",
  },
  IN_PROGRESS: {
    value: "IN_PROGRESS",
    label: "进行中",
    color: "#3B82F6", // blue-500
    bgColor: "bg-blue-500/20",
    textColor: "text-blue-400",
  },
  COMPLETED: {
    value: "COMPLETED",
    label: "已完成",
    color: "#22C55E", // green-500
    bgColor: "bg-green-500/20",
    textColor: "text-green-400",
  },
  DELAYED: {
    value: "DELAYED",
    label: "已延期",
    color: "#EF4444", // red-500
    bgColor: "bg-red-500/20",
    textColor: "text-red-400",
  },
  BLOCKED: {
    value: "BLOCKED",
    label: "受阻",
    color: "#F97316", // orange-500
    bgColor: "bg-orange-500/20",
    textColor: "text-orange-400",
  },
  SKIPPED: {
    value: "SKIPPED",
    label: "已跳过",
    color: "#9CA3AF", // gray-400
    bgColor: "bg-gray-400/20",
    textColor: "text-gray-500",
  },
};

// 阶段分类配置
export const STAGE_CATEGORIES = {
  sales: {
    value: "sales",
    label: "销售阶段",
    color: "#8B5CF6", // violet-500
    bgColor: "bg-violet-500/20",
    icon: "TrendingUp",
  },
  presales: {
    value: "presales",
    label: "售前阶段",
    color: "#06B6D4", // cyan-500
    bgColor: "bg-cyan-500/20",
    icon: "FileText",
  },
  execution: {
    value: "execution",
    label: "执行阶段",
    color: "#3B82F6", // blue-500
    bgColor: "bg-blue-500/20",
    icon: "Wrench",
  },
  closure: {
    value: "closure",
    label: "收尾阶段",
    color: "#22C55E", // green-500
    bgColor: "bg-green-500/20",
    icon: "CheckCircle2",
  },
};

// 健康状态配置
export const HEALTH_STATUS = {
  H1: {
    value: "H1",
    label: "正常",
    color: "#22C55E",
    bgColor: "bg-green-500/20",
    textColor: "text-green-400",
  },
  H2: {
    value: "H2",
    label: "有风险",
    color: "#EAB308",
    bgColor: "bg-yellow-500/20",
    textColor: "text-yellow-400",
  },
  H3: {
    value: "H3",
    label: "阻塞",
    color: "#EF4444",
    bgColor: "bg-red-500/20",
    textColor: "text-red-400",
  },
  H4: {
    value: "H4",
    label: "已完结",
    color: "#6B7280",
    bgColor: "bg-gray-500/20",
    textColor: "text-gray-400",
  },
};

// 评审结果配置
export const REVIEW_RESULTS = {
  PASSED: {
    value: "PASSED",
    label: "通过",
    color: "#22C55E",
    bgColor: "bg-green-500/20",
  },
  CONDITIONAL: {
    value: "CONDITIONAL",
    label: "有条件通过",
    color: "#EAB308",
    bgColor: "bg-yellow-500/20",
  },
  FAILED: {
    value: "FAILED",
    label: "未通过",
    color: "#EF4444",
    bgColor: "bg-red-500/20",
  },
};

// 节点类型配置
export const NODE_TYPES = {
  TASK: {
    value: "TASK",
    label: "任务",
    icon: "CheckSquare",
  },
  APPROVAL: {
    value: "APPROVAL",
    label: "审批",
    icon: "FileCheck",
  },
  DELIVERABLE: {
    value: "DELIVERABLE",
    label: "交付物",
    icon: "FileOutput",
  },
};

// 任务优先级配置
export const TASK_PRIORITIES = {
  LOW: {
    value: "LOW",
    label: "低",
    color: "#6B7280",
  },
  NORMAL: {
    value: "NORMAL",
    label: "普通",
    color: "#3B82F6",
  },
  HIGH: {
    value: "HIGH",
    label: "高",
    color: "#F97316",
  },
  URGENT: {
    value: "URGENT",
    label: "紧急",
    color: "#EF4444",
  },
};

// 视图类型
export const VIEW_TYPES = {
  PIPELINE: "pipeline",
  TIMELINE: "timeline",
  TREE: "tree",
};

// 获取状态颜色的辅助函数
export const getStatusColor = (status) => {
  return STAGE_STATUS[status]?.color || STAGE_STATUS.PENDING.color;
};

export const getStatusConfig = (status) => {
  return STAGE_STATUS[status] || STAGE_STATUS.PENDING;
};

export const getCategoryConfig = (category) => {
  return STAGE_CATEGORIES[category] || STAGE_CATEGORIES.execution;
};

export const getHealthConfig = (health) => {
  return HEALTH_STATUS[health] || HEALTH_STATUS.H1;
};
