import {
  Clock,
  CheckCircle2,
  AlertCircle,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
} from "lucide-react";

/**
 * 获取状态标签配置
 */
export const getStatusBadge = (status) => {
  const badges = {
    IN_PROGRESS: {
      label: "填写中",
      color: "bg-slate-500/20 text-slate-400",
      icon: Clock,
    },
    SUBMITTED: {
      label: "已提交",
      color: "bg-blue-500/20 text-blue-400",
      icon: CheckCircle2,
    },
    EVALUATING: {
      label: "评价中",
      color: "bg-amber-500/20 text-amber-400",
      icon: Clock,
    },
    COMPLETED: {
      label: "已完成",
      color: "bg-emerald-500/20 text-emerald-400",
      icon: CheckCircle2,
    },
    PENDING: {
      label: "待评价",
      color: "bg-orange-500/20 text-orange-400",
      icon: AlertCircle,
    },
  };
  return badges[status] || badges.IN_PROGRESS;
};

/**
 * 获取等级颜色和名称
 */
export const getLevelInfo = (level) => {
  const levels = {
    A: {
      name: "优秀",
      color: "text-emerald-400",
      bgColor: "bg-emerald-500/20",
      borderColor: "border-emerald-500/30",
    },
    B: {
      name: "良好",
      color: "text-blue-400",
      bgColor: "bg-blue-500/20",
      borderColor: "border-blue-500/30",
    },
    C: {
      name: "合格",
      color: "text-amber-400",
      bgColor: "bg-amber-500/20",
      borderColor: "border-amber-500/30",
    },
    D: {
      name: "待改进",
      color: "text-red-400",
      bgColor: "bg-red-500/20",
      borderColor: "border-red-500/30",
    },
  };
  return levels[level] || levels.C;
};

/**
 * 获取趋势图标和颜色
 */
export const getTrendIcon = (current, previous) => {
  if (!previous) return { icon: Minus, color: "text-slate-400" };
  if (current > previous)
    return { icon: ArrowUpRight, color: "text-emerald-400" };
  if (current < previous)
    return { icon: ArrowDownRight, color: "text-red-400" };
  return { icon: Minus, color: "text-slate-400" };
};

/**
 * 计算季度对比数据
 */
export const calculateQuarterComparison = (quarterlyTrend) => {
  if (!quarterlyTrend || quarterlyTrend.length < 2) return null;
  const current = quarterlyTrend[quarterlyTrend.length - 1];
  const previous = quarterlyTrend[quarterlyTrend.length - 2];
  return {
    current: current.score,
    previous: previous.score,
    change: current.score - previous.score,
    percentChange: (
      ((current.score - previous.score) / previous.score) *
      100
    ).toFixed(1),
  };
};
