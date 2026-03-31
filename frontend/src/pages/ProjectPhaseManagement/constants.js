export const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.1 }
  }
};

export const staggerChild = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

export const getStatusBadge = (status) => {
  const badges = {
    PENDING: { label: "待开始", variant: "secondary", color: "text-slate-400" },
    IN_PROGRESS: { label: "进行中", variant: "info", color: "text-blue-400" },
    COMPLETED: {
      label: "已完成",
      variant: "success",
      color: "text-emerald-400"
    },
    SKIPPED: { label: "已跳过", variant: "secondary", color: "text-slate-500" }
  };
  return badges[status] || badges.PENDING;
};

export const getReviewResultBadge = (result) => {
  const badges = {
    PASSED: { label: "通过", variant: "success", color: "text-emerald-400" },
    CONDITIONAL: {
      label: "有条件通过",
      variant: "warning",
      color: "text-yellow-400"
    },
    FAILED: { label: "未通过", variant: "danger", color: "text-red-400" }
  };
  return badges[result] || null;
};
