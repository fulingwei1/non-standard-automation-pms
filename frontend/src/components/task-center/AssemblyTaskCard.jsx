import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Calendar,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  Timer,
  Wrench,
  Package
} from "lucide-react";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";
import { cn } from "../../lib/utils";
import { statusConfigs, priorityConfigs } from "./taskConfig";

/**
 * 装配任务卡片组件（技工专用）
 * 显示物料准备、作业步骤等装配相关信息
 */
export default function AssemblyTaskCard({ task, onStatusChange, onStepToggle }) {
  const [expanded, setExpanded] = useState(true);
  const status = statusConfigs[task.status];
  const priority = priorityConfigs[task.priority];
  const StatusIcon = status.icon;

  const isOverdue = task.status !== "completed" && new Date(task.dueDate) < new Date();
  const partsReady = task.parts?.filter((p) => p.ready).length || 0;
  const partsTotal = task.parts?.length || 0;
  const stepsCompleted = task.instructions?.filter((s) => s.done).length || 0;
  const stepsTotal = task.instructions?.length || 0;

  const handleStatusClick = () => {
    if (task.status === "pending") {
      onStatusChange(task.id, "in_progress");
    } else if (task.status === "in_progress" && stepsCompleted === stepsTotal) {
      onStatusChange(task.id, "completed");
    }
  };

  return (
    <motion.div
      layout
      className={cn(
        "rounded-2xl border overflow-hidden",
        task.status === "blocked"
          ? "bg-red-500/5 border-red-500/30"
          : isOverdue
          ? "bg-amber-500/5 border-amber-500/30"
          : task.status === "in_progress"
          ? "bg-blue-500/5 border-blue-500/30"
          : "bg-surface-1 border-border"
      )}
    >
      {/* Header - larger touch target for workers */}
      <div className="p-5 pb-3">
        <div className="flex items-start gap-4">
          <button
            onClick={handleStatusClick}
            className={cn(
              "p-3 rounded-xl transition-colors",
              status.bgColor,
              task.status !== "blocked" && "hover:bg-accent/20 active:scale-95"
            )}
          >
            <StatusIcon className={cn("w-8 h-8", status.color)} />
          </button>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="outline" className={cn("text-xs", priority.color, "border-current")}>
                {priority.label}优先级
              </Badge>
              {task.machine && (
                <Badge variant="secondary" className="text-xs">
                  {task.machine}
                </Badge>
              )}
            </div>
            <h2 className="text-xl font-bold text-white mb-1">{task.title}</h2>
            <p className="text-sm text-slate-400">
              {task.projectName}
              {task.location && ` · ${task.location}`}
            </p>
          </div>
        </div>

        {/* Block Reason */}
        {task.blockReason && (
          <div className="mt-4 p-4 rounded-xl bg-red-500/10 text-sm text-red-300 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <span>{task.blockReason}</span>
          </div>
        )}

        {/* Progress */}
        {task.status === "in_progress" && stepsTotal > 0 && (
          <div className="mt-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-slate-400">进度</span>
              <span className="text-white font-medium">
                {stepsCompleted}/{stepsTotal} 步骤
              </span>
            </div>
            <Progress value={(stepsCompleted / stepsTotal) * 100 || 0} className="h-2" />
          </div>
        )}

        {/* Time info */}
        <div className="flex items-center gap-6 mt-4 text-sm">
          <span className={cn("flex items-center gap-2", isOverdue ? "text-red-400" : "text-slate-400")}>
            <Calendar className="w-4 h-4" />
            截止: {task.dueDate}
          </span>
          <span className="flex items-center gap-2 text-slate-400">
            <Timer className="w-4 h-4" />
            {task.actualHours}/{task.estimatedHours}h
          </span>
        </div>
      </div>

      {/* Parts checklist */}
      {task.parts && task.parts.length > 0 && (
        <div className="px-5 py-4 border-t border-border/50">
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full flex items-center justify-between text-sm font-medium text-white"
          >
            <span className="flex items-center gap-2">
              <Package className="w-4 h-4 text-blue-400" />
              物料准备 ({partsReady}/{partsTotal})
            </span>
            <motion.span animate={{ rotate: expanded ? 180 : 0 }}>
              <ChevronRight className="w-5 h-5 rotate-90" />
            </motion.span>
          </button>

          <AnimatePresence>
            {expanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="grid grid-cols-2 gap-2 mt-3">
                  {task.parts.map((part, idx) => (
                    <div
                      key={idx}
                      className={cn(
                        "flex items-center gap-2 p-2 rounded-lg text-sm",
                        part.ready ? "bg-emerald-500/10" : "bg-amber-500/10"
                      )}
                    >
                      <div
                        className={cn(
                          "w-5 h-5 rounded-full flex items-center justify-center",
                          part.ready ? "bg-emerald-500" : "bg-amber-500"
                        )}
                      >
                        {part.ready ? (
                          <CheckCircle2 className="w-3 h-3 text-white" />
                        ) : (
                          <Clock className="w-3 h-3 text-white" />
                        )}
                      </div>
                      <span className={part.ready ? "text-emerald-300" : "text-amber-300"}>
                        {part.name} x{part.qty}
                      </span>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Work instructions */}
      {task.instructions && task.instructions.length > 0 && (
        <div className="px-5 py-4 border-t border-border/50">
          <h4 className="flex items-center gap-2 text-sm font-medium text-white mb-3">
            <Wrench className="w-4 h-4 text-violet-400" />
            作业步骤
          </h4>
          <div className="space-y-2">
            {task.instructions.map((step) => (
              <button
                key={step.step}
                onClick={() => onStepToggle(task.id, step.step)}
                className={cn(
                  "w-full flex items-center gap-3 p-3 rounded-xl text-left transition-colors",
                  step.done ? "bg-emerald-500/10" : "bg-surface-2/50 hover:bg-surface-2"
                )}
              >
                <div
                  className={cn(
                    "w-7 h-7 rounded-full border-2 flex items-center justify-center flex-shrink-0",
                    step.done ? "bg-emerald-500 border-emerald-500" : "border-slate-500"
                  )}
                >
                  {step.done ? (
                    <CheckCircle2 className="w-4 h-4 text-white" />
                  ) : (
                    <span className="text-xs text-slate-400">{step.step}</span>
                  )}
                </div>
                <span
                  className={cn(
                    "text-sm",
                    step.done ? "text-emerald-300 line-through" : "text-white"
                  )}
                >
                  {step.desc}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Notes */}
      {task.notes && (
        <div className="px-5 py-3 bg-amber-500/5 border-t border-amber-500/20">
          <p className="text-sm text-amber-300 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            {task.notes}
          </p>
        </div>
      )}

      {/* Tools needed */}
      {task.tools && task.tools.length > 0 && (
        <div className="px-5 py-3 bg-surface-2/30 border-t border-border/30">
          <p className="text-xs text-slate-400">
            <span className="font-medium">所需工具：</span>
            {task.tools.join("、")}
          </p>
        </div>
      )}
    </motion.div>
  );
}
