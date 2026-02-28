/**
 * 竞品分析组件
 * 展示竞争对手信息和比较
 */
import { motion } from "framer-motion";
import {
  Shield,
  Award,
  ThumbsDown,
  HelpCircle,
  DollarSign,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import { Badge } from "../ui/badge";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

export function CompetitorAnalysis({ competitors, className }) {
  if (!competitors || competitors.length === 0) {
    return (
      <div className="text-center py-6 text-slate-400">
        <Shield className="w-8 h-8 mx-auto mb-2 text-slate-600" />
        <p className="text-sm">暂无竞争对手信息</p>
      </div>
    );
  }

  const getStatusConfig = (status) => {
    switch (status) {
      case "confirmed":
        return { text: "已确认", color: "bg-blue-500", icon: Shield };
      case "rumored":
        return { text: "传闻", color: "bg-slate-500", icon: HelpCircle };
      case "won":
        return { text: "中标", color: "bg-emerald-500", icon: Award };
      case "lost":
        return { text: "未中标", color: "bg-red-500", icon: ThumbsDown };
      default:
        return { text: "未知", color: "bg-slate-500", icon: HelpCircle };
    }
  };

  return (
    <motion.div variants={fadeIn} className={cn("space-y-3", className)}>
      {competitors.map((competitor, index) => {
        const statusConfig = getStatusConfig(competitor.status);
        const StatusIcon = statusConfig.icon;

        return (
          <div
            key={index}
            className="flex items-center justify-between p-3 bg-surface-50 rounded-lg"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center">
                <StatusIcon className="w-4 h-4 text-red-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-white">
                  {competitor.name}
                </p>
                <Badge className={cn("text-xs mt-1", statusConfig.color)}>
                  {statusConfig.text}
                </Badge>
              </div>
            </div>
            <div className="text-right">
              {competitor.price && (
                <p className="text-sm text-slate-400 flex items-center gap-1">
                  <DollarSign className="w-3 h-3" />
                  {competitor.price}
                </p>
              )}
              {competitor.strength && (
                <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                  <TrendingUp className="w-3 h-3 text-emerald-400" />
                  优势: {competitor.strength}
                </p>
              )}
              {competitor.weakness && (
                <p className="text-xs text-slate-500 flex items-center gap-1">
                  <TrendingDown className="w-3 h-3 text-red-400" />
                  劣势: {competitor.weakness}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </motion.div>
  );
}

export default CompetitorAnalysis;
