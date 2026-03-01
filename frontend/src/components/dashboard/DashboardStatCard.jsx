/**
 * DashboardStatCard - 统一的工作台统计卡片组件
 * 提供一致的设计和交互体验
 *
 * @param {Object} props
 * @param {React.Component} props.icon - Lucide图标组件
 * @param {string} props.label - 标签文本
 * @param {string|number} props.value - 显示值
 * @param {string} props.change - 变化值
 * @param {'up'|'down'|'neutral'} props.trend - 趋势方向
 * @param {string} props.description - 描述文本
 * @param {Function} props.onClick - 点击回调
 * @param {boolean} props.loading - 加载状态
 * @param {string} props.className - CSS类名
 * @param {string} props.iconColor - 图标颜色
 * @param {string} props.iconBg - 图标背景
 */
import { memo } from "react";
import { motion } from "framer-motion";
import { DashboardStatCard as UiStatCard } from "../ui/card";

const DashboardStatCard = memo(function DashboardStatCard({
  icon: Icon,
  label,
  value,
  change,
  trend,
  description,
  onClick,
  loading = false,
  className,
  iconColor = "text-primary",
  iconBg = "bg-gradient-to-br from-primary/20 to-indigo-500/10",
}) {
  return (
    <motion.div
      whileHover={onClick ? { scale: 1.02 } : undefined}
      whileTap={onClick ? { scale: 0.98 } : undefined}
    >
      <UiStatCard
        icon={Icon}
        label={label}
        value={value || "unknown"}
        change={change}
        trend={trend}
        description={description}
        onClick={onClick}
        loading={loading}
        className={className}
        iconColor={iconColor}
        iconBg={iconBg}
      />
    </motion.div>
  );
});

DashboardStatCard.displayName = "DashboardStatCard";

export default DashboardStatCard;
