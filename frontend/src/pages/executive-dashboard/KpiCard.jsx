import { motion } from "framer-motion";
import { TrendingUp, TrendingDown } from "lucide-react";
import { Card, CardContent } from "../../components/ui";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { colorMap, iconColorMap } from "./constants";

export function KpiCard({ kpi }) {
  const Icon = kpi.icon;
  return (
    <motion.div variants={fadeIn}>
      <Card className={cn("bg-gradient-to-br border", colorMap[kpi.color])}>
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-sm text-slate-400 mb-1">{kpi.title}</p>
              <p className="text-2xl font-bold text-white">{kpi.value}</p>
              <div className="flex items-center gap-2 mt-2">
                <span
                  className={cn(
                    "text-xs flex items-center gap-1",
                    kpi.changeType === "up"
                      ? "text-emerald-400"
                      : "text-red-400"
                  )}
                >
                  {kpi.changeType === "up" ? (
                    <TrendingUp className="w-3 h-3" />
                  ) : (
                    <TrendingDown className="w-3 h-3" />
                  )}
                  {kpi.change}
                </span>
                <span className="text-xs text-slate-500">{kpi.subText}</span>
              </div>
            </div>
            <div className={cn("p-3 rounded-xl", iconColorMap[kpi.color])}>
              <Icon className="w-6 h-6" />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
