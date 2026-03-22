/**
 * 技术评估工作台 - 常量、配置对象和工具函数
 */

// 决策配置（支持英文枚举和中文标签两种 key）
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
  推荐立项: {
    label: "推荐立项",
    color: "bg-green-500",
    textColor: "text-green-400",
  },
  有条件立项: {
    label: "有条件立项",
    color: "bg-yellow-500",
    textColor: "text-yellow-400",
  },
  暂缓: {
    label: "暂缓",
    color: "bg-orange-500",
    textColor: "text-orange-400",
  },
  不建议立项: {
    label: "不建议立项",
    color: "bg-red-500",
    textColor: "text-red-400",
  },
};

// 评估状态配置
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
  SKIPPED: {
    label: "已跳过",
    color: "bg-slate-500",
    textColor: "text-slate-300",
  },
};

// 评估维度标签
export const dimensionLabels = {
  technology: "技术",
  business: "商务",
  resource: "资源",
  delivery: "交付",
  customer: "客户关系",
};

// 漏斗实体标签
export const funnelEntityLabels = {
  LEAD: "线索",
  OPPORTUNITY: "商机",
  QUOTE: "报价",
  CONTRACT: "合同",
};

// 空列表占位结构
export const emptyListPayload = {
  items: [],
  total: 0,
};

// --- 工具函数 ---

// 安全解析 JSON，兼容对象和字符串
export function safeJsonParse(value, fallback) {
  if (!value) {
    return fallback;
  }
  if (typeof value === "object") {
    return value;
  }
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

// 归一化维度评分，兼容后端不同字段名
export function normalizeDimensionScores(rawScores) {
  const scores = safeJsonParse(rawScores, {});
  const normalized = {
    technology: scores.technology ?? scores.technical ?? 0,
    business: scores.business ?? scores.commercial ?? 0,
    resource: scores.resource ?? 0,
    delivery: scores.delivery ?? scores.timeline ?? 0,
    customer: scores.customer ?? scores.risk ?? 0,
  };
  return Object.values(normalized).some((score) => score !== 0) ? normalized : null;
}

// 格式化日期，支持带时间和不带时间两种模式
export function formatDate(value, withTime = true) {
  if (!value) {
    return "未记录";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return withTime ? date.toLocaleString() : date.toLocaleDateString();
}

// 格式化来源类型
export function formatSourceType(sourceType) {
  return sourceType === "lead" ? "线索" : "商机";
}

// 序列化需求详情为 JSON 文本
export function buildRequirementText(requirementDetail) {
  if (!requirementDetail) {
    return "{}";
  }
  return JSON.stringify(requirementDetail, null, 2);
}

// 获取决策元信息（label + color）
export function getDecisionMeta(decision) {
  return decisionConfig[decision] || {
    label: decision || "未生成",
    color: "bg-slate-500",
    textColor: "text-slate-300",
  };
}

// 获取状态元信息（label + color）
export function getStatusMeta(status) {
  return statusConfig[status] || {
    label: status || "未知",
    color: "bg-slate-500",
    textColor: "text-slate-300",
  };
}

// 根据风险等级返回对应的 badge 颜色
export function getRiskLevelBadge(level) {
  if (level === "CRITICAL" || level === "HIGH") {
    return "bg-red-500";
  }
  if (level === "MEDIUM") {
    return "bg-yellow-500";
  }
  return "bg-slate-500";
}
