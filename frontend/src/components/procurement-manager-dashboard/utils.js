export const getStatusColor = (status) => {
  const colors = {
    active: "bg-emerald-500",
    pending: "bg-amber-500",
    processing: "bg-blue-500",
    completed: "bg-slate-500",
    excellent: "bg-emerald-500",
    good: "bg-blue-500",
    warning: "bg-amber-500"
  };
  return colors[status] || "bg-slate-500";
};

export const getStatusLabel = (status) => {
  const labels = {
    active: "正常",
    pending: "待处理",
    processing: "处理中",
    completed: "已完成",
    excellent: "优秀",
    good: "良好",
    warning: "需关注"
  };
  return labels[status] || status;
};

export const getPriorityColor = (priority) => {
  const colors = {
    high: "bg-red-500",
    medium: "bg-amber-500",
    low: "bg-blue-500"
  };
  return colors[priority] || "bg-slate-500";
};

export const getAlertLevelColor = (level) => {
  const colors = {
    critical: "bg-red-500",
    warning: "bg-amber-500",
    info: "bg-blue-500"
  };
  return colors[level] || "bg-slate-500";
};
