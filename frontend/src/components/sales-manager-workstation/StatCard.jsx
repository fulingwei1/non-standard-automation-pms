import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import { Card, CardContent } from "../../components/ui";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

export function StatCard({ title, value, subtitle, trend, icon: Icon, color, bg }) {
  const [isHovered, setIsHovered] = useState(false);
  
  return (
    <motion.div
      variants={fadeIn}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
    >
      <Card
        className={cn(
          "transition-all duration-300",
          isHovered && "scale-105",
          bg,
          "border-slate-700/50"
        )}
      >
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-xs text-slate-400 mb-1">{title}</p>
              <p className={cn("text-xl font-bold text-white", color)}>
                {value}
              </p>
              <p className="text-xs text-slate-400 mt-1">{subtitle}</p>
              {trend !== undefined && (
                <div
                  className={cn(
                    "flex items-center text-xs mt-1",
                    trend > 0 ? "text-emerald-400" : "text-red-400"
                  )}
                >
                  {trend > 0 ? (
                    <ArrowUpRight className="w-3 h-3 mr-1" />
                  ) : (
                    <ArrowDownRight className="w-3 h-3 mr-1" />
                  )}
                  {Math.abs(trend)}%
                </div>
              )}
            </div>
            <div className={cn("p-2 rounded-lg", bg)}>
              <Icon className={cn("w-5 h-5", color)} />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
