import { motion } from "framer-motion";
import { TrendingUp } from "lucide-react";
import { Card, CardContent } from "../../ui/card";
import { cn } from "../../../lib/utils";
import { fadeIn } from "../../../lib/animations";

export default function StatsCards({ stats }) {
  return (
    <motion.div
      variants={fadeIn}
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
    >
      {stats.map((stat) => (
        <Card
          key={stat.id}
          className="bg-surface-100/50 backdrop-blur-lg border border-white/5 shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
        >
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm text-slate-400">{stat.title}</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {stat.value}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-slate-500">
                    {stat.subtitle}
                  </span>
                  {stat.trend && (
                    <span className="text-xs text-emerald-400 flex items-center gap-0.5">
                      <TrendingUp className="w-3 h-3" />
                      {stat.trend}
                    </span>
                  )}
                </div>
              </div>
              <div
                className={cn(
                  "w-10 h-10 rounded-xl flex items-center justify-center",
                  stat.bgColor
                )}
              >
                <stat.icon className={cn("w-5 h-5", stat.color)} />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </motion.div>
  );
}
