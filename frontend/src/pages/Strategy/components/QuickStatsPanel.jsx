/**
 * 快速统计面板组件
 * 展示战略关键统计数据
 */
import { motion } from "framer-motion";
import {
  Target,
  CheckCircle2,
  AlertCircle,
  XCircle,
  TrendingUp,
  Users,
  Calendar,
  Award,
} from "lucide-react";
import { Card, CardContent } from "../../../components/ui";
import { cn } from "../../../lib/utils";
import { fadeIn, staggerContainer } from "../../../lib/animations";

const statItems = [
  {
    key: "total_strategies",
    label: "战略数量",
    icon: Target,
    color: "text-primary",
    bg: "bg-primary/10",
  },
  {
    key: "active_strategies",
    label: "执行中",
    icon: CheckCircle2,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
  },
  {
    key: "total_kpis",
    label: "KPI总数",
    icon: TrendingUp,
    color: "text-blue-400",
    bg: "bg-blue-500/10",
  },
  {
    key: "kpi_on_track",
    label: "KPI达标",
    icon: Award,
    color: "text-green-400",
    bg: "bg-green-500/10",
  },
  {
    key: "kpi_at_risk",
    label: "KPI预警",
    icon: AlertCircle,
    color: "text-amber-400",
    bg: "bg-amber-500/10",
  },
  {
    key: "kpi_off_track",
    label: "KPI落后",
    icon: XCircle,
    color: "text-red-400",
    bg: "bg-red-500/10",
  },
  {
    key: "total_annual_works",
    label: "年度工作",
    icon: Calendar,
    color: "text-purple-400",
    bg: "bg-purple-500/10",
  },
  {
    key: "personal_kpi_coverage",
    label: "个人KPI覆盖",
    icon: Users,
    color: "text-cyan-400",
    bg: "bg-cyan-500/10",
    suffix: "%",
  },
];

export function QuickStatsPanel({ stats }) {
  if (!stats) return null;

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3"
    >
      {(statItems || []).map((item) => {
        const Icon = item.icon;
        const value = stats[item.key] ?? 0;
        const displayValue = item.suffix ? `${value}${item.suffix}` : value;

        return (
          <motion.div key={item.key} variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50 hover:border-slate-600/80 transition-all">
              <CardContent className="p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className={cn("p-1.5 rounded-lg", item.bg)}>
                    <Icon className={cn("w-3.5 h-3.5", item.color)} />
                  </div>
                </div>
                <div className="text-xl font-bold text-white">{displayValue}</div>
                <p className="text-xs text-slate-400 mt-0.5">{item.label}</p>
              </CardContent>
            </Card>
          </motion.div>
        );
      })}
    </motion.div>
  );
}
