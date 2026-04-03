/**
 * Timeline stage component for order lifecycle visualization
 */

import { motion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";
import { cn } from "../../lib/utils";
import { formatDate } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { statusConfig } from "./constants";

const TimelineStage = ({ stage, idx, total }) => {
  const config = statusConfig[stage.stage] || {};
  const isCompleted = stage.status === "completed";
  const isPending = stage.status === "pending";

  return (
    <div className="relative flex flex-col items-center">
      <motion.div
        variants={fadeIn}
        className="flex flex-col items-center w-full mb-4"
      >
        <div
          className={cn(
            "w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all",
            isCompleted
              ? "bg-emerald-500/20 border-emerald-500 text-emerald-400"
              : isPending
                ? "bg-amber-500/20 border-amber-500 text-amber-400"
                : "bg-slate-600/30 border-slate-600 text-slate-400"
          )}
        >
          {config.icon ? (
            <config.icon className="w-5 h-5" />
          ) : (
            <CheckCircle2 className="w-5 h-5" />
          )}
        </div>
        <p className="mt-2 font-medium text-sm text-slate-100">{stage.label}</p>
        {stage.date && (
          <p className="text-xs text-slate-500 mt-1">
            {formatDate(stage.date)}
          </p>
        )}
        {stage.daysLeft && (
          <p className="text-xs text-amber-400 mt-1">
            \u8fd8\u9700 {stage.daysLeft} \u5929
          </p>
        )}
        <p className="text-xs text-slate-400 mt-1">{stage.description}</p>
      </motion.div>

      {idx < total - 1 && (
        <div
          className={cn(
            "w-0.5 h-16 -mb-4",
            isCompleted ? "bg-emerald-500/40" : "bg-slate-600/30"
          )}
        />
      )}
    </div>
  );
};

export default TimelineStage;
