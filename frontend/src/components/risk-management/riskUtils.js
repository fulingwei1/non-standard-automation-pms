/**
 * 风险管理 - 工具函数
 */

// 风险等级徽章配置
export const getRiskLevelBadge = (level) => {
  const badges = {
    CRITICAL: {
      label: "严重",
      variant: "danger",
      color: "text-red-400",
      bgColor: "bg-red-500/20",
      borderColor: "border-red-500/30",
    },
    HIGH: {
      label: "高",
      variant: "danger",
      color: "text-orange-400",
      bgColor: "bg-orange-500/20",
      borderColor: "border-orange-500/30",
    },
    MEDIUM: {
      label: "中",
      variant: "warning",
      color: "text-yellow-400",
      bgColor: "bg-yellow-500/20",
      borderColor: "border-yellow-500/30",
    },
    LOW: {
      label: "低",
      variant: "info",
      color: "text-blue-400",
      bgColor: "bg-blue-500/20",
      borderColor: "border-blue-500/30",
    },
  };
  return badges[level] || badges.LOW;
};

// 状态徽章配置
export const getStatusBadge = (status) => {
  const badges = {
    IDENTIFIED: { label: "已识别", variant: "secondary" },
    ANALYZING: { label: "分析中", variant: "info" },
    RESPONDING: { label: "应对中", variant: "warning" },
    MONITORING: { label: "监控中", variant: "info" },
    CLOSED: { label: "已关闭", variant: "success" },
  };
  return badges[status] || badges.IDENTIFIED;
};

// 概率标签
export const getProbabilityLabel = (prob) => {
  const labels = {
    HIGH: "高",
    MEDIUM: "中",
    LOW: "低",
  };
  return labels[prob] || "未知";
};

// 影响标签
export const getImpactLabel = (impact) => {
  const labels = {
    HIGH: "高",
    MEDIUM: "中",
    LOW: "低",
  };
  return labels[impact] || "未知";
};
