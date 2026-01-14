/**
 * DashboardStatCard - 统一的工作台统计卡片组件
 * 提供一致的设计和交互体验
 */
import { memo } from "react";
import { motion } from "framer-motion";
import { cn } from "../../lib/utils";
import { Card } from "../ui/card";
import { LucideIcon } from "lucide-react";

export interface DashboardStatCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  change?: string;
  trend?: "up" | "down" | "neutral";
  description?: string;
  onClick?: () => void;
  loading?: boolean;
  className?: string;
  iconColor?: string;
  iconBg?: string;
}

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
}: DashboardStatCardProps) {
  if (loading) {
    return (
      <Card className={cn("p-5", className)}>
        <div className="animate-pulse">
          <div className="h-10 w-10 rounded-xl bg-white/10 mb-4" />
          <div className="h-3 w-20 rounded bg-white/10 mb-3" />
          <div className="h-6 w-16 rounded bg-white/10" />
        </div>
      </Card>
    );
  }

  const trendConfig = {
    up: {
      text: "text-emerald-400",
      bg: "bg-emerald-500/10",
      symbol: "↑",
    },
    down: {
      text: "text-red-400",
      bg: "bg-red-500/10",
      symbol: "↓",
    },
    neutral: {
      text: "text-slate-400",
      bg: "bg-slate-500/10",
      symbol: "",
    },
  };

  const config = trendConfig[trend || "neutral"];

  return (
    <motion.div
      whileHover={onClick ? { scale: 1.02 } : undefined}
      whileTap={onClick ? { scale: 0.98 } : undefined}
    >
      <Card
        hover={!!onClick}
        className={cn("p-5 group", onClick && "cursor-pointer", className)}
        onClick={onClick}
      >
        <div className="flex items-center justify-between mb-4">
          <div
            className={cn(
              "p-2.5 rounded-xl",
              iconBg,
              "ring-1 ring-primary/20",
            )}
          >
            <Icon className={cn("h-5 w-5", iconColor)} />
          </div>

          {change && trend && (
            <div
              className={cn(
                "flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full",
                config.text,
                config.bg,
              )}
            >
              {config.symbol}
              {change}
            </div>
          )}
        </div>

        <p className="text-sm text-slate-400 mb-1">{label}</p>
        <p className="text-2xl font-semibold text-white tracking-tight">
          {value}
        </p>
        {description && (
          <p className="text-xs text-slate-500 mt-1">{description}</p>
        )}
      </Card>
    </motion.div>
  );
});

DashboardStatCard.displayName = "DashboardStatCard";

export default DashboardStatCard;
