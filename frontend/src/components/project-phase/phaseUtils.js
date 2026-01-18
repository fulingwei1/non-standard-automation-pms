/**
 * 项目阶段管理 - 工具函数
 */

// 状态徽章配置
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

// 评审结果徽章配置
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
