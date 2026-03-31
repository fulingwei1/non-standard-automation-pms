import { motion } from "framer-motion";
import {
  Layers,
  CheckCircle,
  Star,
  Settings,
  FileText,
} from "lucide-react";
import { Card, CardContent } from "../../components/ui/card";
import { cn } from "../../lib/utils";
import { fadeIn, staggerContainer } from "../../lib/animations";

const STAT_CONFIG = [
  { key: "total", label: "模板总数", icon: Layers, color: "text-violet-400" },
  { key: "active", label: "已启用", icon: CheckCircle, color: "text-emerald-400" },
  { key: "default", label: "默认模板", icon: Star, color: "text-amber-400" },
  { key: "totalStages", label: "阶段总数", icon: Settings, color: "text-blue-400" },
  { key: "totalNodes", label: "节点总数", icon: FileText, color: "text-purple-400" },
];

export default function StatsCards({ stats }) {
  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="show"
      className="grid grid-cols-1 md:grid-cols-5 gap-4"
    >
      {STAT_CONFIG.map((stat) => (
        <motion.div key={stat.label} variants={fadeIn}>
          <Card className="bg-surface-100 border-white/5 hover:border-white/10 transition-colors">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">{stat.label}</p>
                  <p className={cn("text-2xl font-bold mt-1", stat.color)}>
                    {stats[stat.key]}
                  </p>
                </div>
                <div className={cn("p-3 rounded-xl bg-white/5", stat.color)}>
                  <stat.icon className="h-5 w-5" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </motion.div>
  );
}
