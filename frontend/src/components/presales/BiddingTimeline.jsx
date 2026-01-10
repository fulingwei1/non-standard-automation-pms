/**
 * 投标时间线组件
 * 展示投标项目的关键节点和进度
 */
import React from "react";
import { motion } from "framer-motion";
import { CheckCircle, Clock, Flag, AlertTriangle } from "lucide-react";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

export function BiddingTimeline({ timeline, className }) {
  if (!timeline || timeline.length === 0) {
    return null;
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case "completed":
        return {
          icon: CheckCircle,
          color: "bg-emerald-500",
          textColor: "text-emerald-500",
        };
      case "in_progress":
        return {
          icon: Clock,
          color: "bg-blue-500",
          textColor: "text-blue-500",
        };
      case "pending":
        return {
          icon: Flag,
          color: "bg-slate-600",
          textColor: "text-slate-500",
        };
      case "overdue":
        return {
          icon: AlertTriangle,
          color: "bg-red-500",
          textColor: "text-red-500",
        };
      default:
        return {
          icon: Flag,
          color: "bg-slate-600",
          textColor: "text-slate-500",
        };
    }
  };

  return (
    <motion.div variants={fadeIn} className={cn("space-y-4", className)}>
      {timeline.map((item, index) => {
        const statusConfig = getStatusIcon(item.status);
        const StatusIcon = statusConfig.icon;

        return (
          <div key={index} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "w-6 h-6 rounded-full flex items-center justify-center",
                  statusConfig.color,
                )}
              >
                <StatusIcon className="w-3 h-3 text-white" />
              </div>
              {index < timeline.length - 1 && (
                <div
                  className={cn(
                    "w-px h-8 my-1",
                    item.status === "completed"
                      ? "bg-emerald-500"
                      : "bg-slate-700",
                  )}
                />
              )}
            </div>
            <div className="flex-1">
              <p
                className={cn(
                  "text-sm",
                  item.status === "completed" ? "text-white" : "text-slate-400",
                )}
              >
                {item.event}
              </p>
              <p className="text-xs text-slate-500">{item.date}</p>
              {item.note && (
                <p className="text-xs text-slate-400 mt-1">{item.note}</p>
              )}
            </div>
          </div>
        );
      })}
    </motion.div>
  );
}

export default BiddingTimeline;
