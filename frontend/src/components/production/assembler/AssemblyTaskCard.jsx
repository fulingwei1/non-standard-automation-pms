import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  AlertTriangle,
  User,
  Calendar,
  Timer,
  MapPin,
  Package,
  ChevronRight,
  CheckCircle2,
  Wrench,
  MessageSquare,
  FileImage,
  PlayCircle,
  FileWarning,
} from "lucide-react";
import {
  Button,
  Badge,
  Progress,
} from "../../ui";
import { cn } from "../../../lib/utils";
import { statusConfigs, priorityConfigs } from "./utils";

export default function AssemblyTaskCard({ task, onAction }) {
  const [expanded, setExpanded] = useState(false);
  const [materialsExpanded, setMaterialsExpanded] = useState(false);
  const status = statusConfigs[task.status];
  const priority = priorityConfigs[task.priority];
  const StatusIcon = status.icon;

  const hasShortage = task.materials?.some((m) => m.status === "shortage");
  const completedSteps = task.steps?.filter((s) => s.completed).length || 0;
  const totalSteps = task.steps?.length || 0;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "rounded-xl border overflow-hidden",
        task.status === "blocked"
          ? "bg-red-500/5 border-red-500/30"
          : hasShortage
          ? "bg-amber-500/5 border-amber-500/30"
          : "bg-surface-1 border-border"
      )}
    >
      <div className="p-4">
        <div className="flex items-start gap-3 mb-3">
          <div className={cn("p-2 rounded-lg", status.bgColor)}>
            <StatusIcon className={cn("w-5 h-5", status.color)} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Badge
                className={cn("text-xs", priority.bgColor, priority.color)}
              >
                {priority.label}优先级
              </Badge>
              <Badge variant="outline" className="text-xs">
                {task.machineNo}
              </Badge>
            </div>
            <h3 className="font-semibold text-white text-lg">{task.title}</h3>
            <p className="text-sm text-slate-400">
              {task.projectName} · {task.workstation}
            </p>
          </div>
        </div>

        {task.blockReason && (
          <div className="mb-3 p-2 rounded-lg bg-red-500/10 text-sm text-red-300 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            {task.blockReason}
          </div>
        )}

        {task.status !== "completed" && (
          <div className="mb-3">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-slate-400">进度</span>
              <span className="text-white">
                {completedSteps}/{totalSteps} 步骤
              </span>
            </div>
            <Progress
              value={(completedSteps / totalSteps) * 100}
              className="h-2"
            />
          </div>
        )}

        <div className="flex items-center flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400 mb-3">
          <span className="flex items-center gap-1">
            <User className="w-3.5 h-3.5 text-primary" />
            <span className="text-white font-medium">{task.assignee}</span>
          </span>
          <span className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5" />
            截止: {task.dueDate}
          </span>
          <span className="flex items-center gap-1">
            <Timer className="w-3.5 h-3.5" />
            {task.actualHours}/{task.estimatedHours}h
          </span>
          <span className="flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5" />
            {task.workstation}
          </span>
        </div>

        {task.materials?.length > 0 && (
          <div className="mb-3">
            <button
              onClick={() => setMaterialsExpanded(!materialsExpanded)}
              className="w-full flex items-center justify-between py-2 text-sm"
            >
              <span className="flex items-center gap-2">
                <Package
                  className={cn(
                    "w-4 h-4",
                    hasShortage ? "text-amber-400" : "text-emerald-400"
                  )}
                />
                <span className="text-slate-300">
                  物料准备 (
                  {task.materials.filter((m) => m.status === "ok").length}/
                  {task.materials.length})
                </span>
                {hasShortage && (
                  <Badge className="text-[10px] bg-amber-500/20 text-amber-400">
                    有缺料
                  </Badge>
                )}
              </span>
              <ChevronRight
                className={cn(
                  "w-4 h-4 text-slate-400 transition-transform",
                  materialsExpanded && "rotate-90"
                )}
              />
            </button>

            <AnimatePresence>
              {materialsExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div className="space-y-2 pt-2">
                    {task.materials.map((material) => (
                      <div
                        key={material.id}
                        className={cn(
                          "flex items-center justify-between p-2 rounded-lg",
                          material.status === "shortage"
                            ? "bg-amber-500/10"
                            : "bg-surface-2/50"
                        )}
                      >
                        <div className="flex items-center gap-2">
                          {material.status === "ok" ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          ) : (
                            <AlertTriangle className="w-4 h-4 text-amber-400" />
                          )}
                          <div>
                            <p className="text-sm text-white">
                              {material.name}
                            </p>
                            <p className="text-xs text-slate-400">
                              {material.spec} × {material.received}/
                              {material.qty}
                            </p>
                          </div>
                        </div>
                        {material.status === "shortage" && (
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 text-xs text-amber-400"
                              onClick={() =>
                                onAction("shortage", task, material)
                              }
                            >
                              反馈缺料
                            </Button>
                          </div>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-slate-400"
                          onClick={() => onAction("quality", task, material)}
                        >
                          <FileWarning className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {task.steps?.length > 0 && (
          <div className="mb-3">
            <button
              onClick={() => setExpanded(!expanded)}
              className="w-full flex items-center justify-between py-2 text-sm"
            >
              <span className="flex items-center gap-2">
                <Wrench className="w-4 h-4 text-blue-400" />
                <span className="text-slate-300">作业步骤</span>
              </span>
              <ChevronRight
                className={cn(
                  "w-4 h-4 text-slate-400 transition-transform",
                  expanded && "rotate-90"
                )}
              />
            </button>

            <AnimatePresence>
              {expanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div className="space-y-2 pt-2">
                    {task.steps.map((step, index) => (
                      <button
                        key={step.id}
                        className={cn(
                          "w-full flex items-center gap-3 p-2 rounded-lg text-left",
                          "transition-all hover:bg-surface-2",
                          step.completed ? "opacity-60" : ""
                        )}
                      >
                        <div
                          className={cn(
                            "w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0",
                            step.completed
                              ? "bg-emerald-500 border-emerald-500"
                              : "border-slate-500"
                          )}
                        >
                          {step.completed ? (
                            <CheckCircle2 className="w-4 h-4 text-white" />
                          ) : (
                            <span className="text-xs text-slate-400">
                              {index + 1}
                            </span>
                          )}
                        </div>
                        <span
                          className={cn(
                            "text-sm",
                            step.completed
                              ? "text-slate-500 line-through"
                              : "text-slate-200"
                          )}
                        >
                          {step.title}
                        </span>
                      </button>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {task.notes && (
          <div className="mb-3 p-2 rounded-lg bg-blue-500/10 text-sm text-blue-300 flex items-start gap-2">
            <MessageSquare className="w-4 h-4 flex-shrink-0 mt-0.5" />
            {task.notes}
          </div>
        )}

        {task.tools?.length > 0 && (
          <p className="text-xs text-slate-500 mb-3">
            所需工具：{task.tools.join("、")}
          </p>
        )}

        <div className="flex items-center gap-2 pt-3 border-t border-border/50">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => onAction("drawing", task)}
          >
            <FileImage className="w-4 h-4 mr-1" />
            查看图纸
          </Button>

          {task.status === "in_progress" && (
            <Button
              size="sm"
              className="flex-1 bg-emerald-500 hover:bg-emerald-600"
              onClick={() => onAction("complete", task)}
            >
              <CheckCircle2 className="w-4 h-4 mr-1" />
              确认完成
            </Button>
          )}

          {task.status === "pending" && !task.blockedBy && (
            <Button
              size="sm"
              className="flex-1"
              onClick={() => onAction("start", task)}
            >
              <PlayCircle className="w-4 h-4 mr-1" />
              开始任务
            </Button>
          )}
        </div>
      </div>
    </motion.div>
  );
}
