import { motion } from "framer-motion";
import { FolderKanban, Target, Truck, AlertTriangle } from "lucide-react";
import { Card, CardContent } from "../../components/ui";
import { fadeIn } from "../../lib/animations";

/**
 * StatsRow — four summary stat cards at the top of the Sales Project Track page.
 */
export function StatsRow({ stats }) {
  const cards = [
    {
      icon: <FolderKanban className="w-5 h-5 text-blue-400" />,
      iconBg: "bg-blue-500/20",
      value: stats.total,
      label: "我的项目",
    },
    {
      icon: <Target className="w-5 h-5 text-emerald-400" />,
      iconBg: "bg-emerald-500/20",
      value: stats.inProgress,
      label: "进行中",
    },
    {
      icon: <Truck className="w-5 h-5 text-amber-400" />,
      iconBg: "bg-amber-500/20",
      value: stats.nearDelivery,
      label: "近期交付",
    },
    {
      icon: <AlertTriangle className="w-5 h-5 text-red-400" />,
      iconBg: "bg-red-500/20",
      value: stats.hasIssue,
      label: "需关注",
    },
  ];

  return (
    <motion.div
      variants={fadeIn}
      className="grid grid-cols-2 sm:grid-cols-4 gap-4"
    >
      {cards.map(({ icon, iconBg, value, label }) => (
        <Card key={label} className="bg-surface-100/50">
          <CardContent className="p-4 flex items-center gap-4">
            <div className={`p-2 ${iconBg} rounded-lg`}>{icon}</div>
            <div>
              <p className="text-2xl font-bold text-white">{value}</p>
              <p className="text-xs text-slate-400">{label}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </motion.div>
  );
}
