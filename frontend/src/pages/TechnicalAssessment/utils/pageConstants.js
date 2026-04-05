/**
 * Page-specific constants for TechnicalAssessment
 */

export const decisionConfig = {
  RECOMMEND: {
    label: "推荐立项",
    color: "bg-green-500",
    textColor: "text-green-400",
  },
  CONDITIONAL: {
    label: "有条件立项",
    color: "bg-yellow-500",
    textColor: "text-yellow-400",
  },
  DEFER: {
    label: "暂缓",
    color: "bg-orange-500",
    textColor: "text-orange-400",
  },
  NOT_RECOMMEND: {
    label: "不建议立项",
    color: "bg-red-500",
    textColor: "text-red-400",
  },
};

export const statusConfig = {
  PENDING: {
    label: "待评估",
    color: "bg-gray-500",
    textColor: "text-gray-400",
  },
  IN_PROGRESS: {
    label: "评估中",
    color: "bg-blue-500",
    textColor: "text-blue-400",
  },
  COMPLETED: {
    label: "已完成",
    color: "bg-green-500",
    textColor: "text-green-400",
  },
  CANCELLED: {
    label: "已取消",
    color: "bg-red-500",
    textColor: "text-red-400",
  },
};

export const dimensionLabels = {
  technology: "技术",
  business: "商务",
  resource: "资源",
  delivery: "交付",
  customer: "客户关系",
};

export const dimensionNames = {
  technology: "技术维度",
  business: "商务维度",
  resource: "资源维度",
  delivery: "交付维度",
  customer: "客户关系维度",
};
