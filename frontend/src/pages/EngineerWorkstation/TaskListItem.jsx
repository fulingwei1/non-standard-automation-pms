/**
 * TaskListItem - Individual task row for list and project views
 */





import { cn } from "../../lib/utils";
import { statusConfigs, priorityConfigs, taskTypeConfigs } from "./constants";

export default function TaskListItem({ task, onClick, isSelected }) {
  const status = statusConfigs[task.status];
  const priority = priorityConfigs[task.priority];
  const taskType = taskTypeConfigs[task.type];
  const StatusIcon = status.icon;
  const TypeIcon = taskType.icon;

  const isOverdue =
  task.status !== "completed" && new Date(task.plannedEnd) < new Date();
  const daysUntilDue = Math.ceil(
    (new Date(task.plannedEnd) - new Date()) / (1000 * 60 * 60 * 24)
  );

  return (
    <motion.div
      layout
      whileHover={{ scale: 1.005 }}
      onClick={() => onClick(task)}
      className={cn(
        "rounded-xl border p-4 cursor-pointer transition-all",
        isSelected ?
        "bg-primary/10 border-primary/30" :
        task.status === "blocked" ?
        "bg-red-500/5 border-red-500/30 hover:border-red-500/50" :
        isOverdue ?
        "bg-amber-500/5 border-amber-500/30 hover:border-amber-500/50" :
        "bg-surface-1/50 border-border hover:border-border/80"
      )}>

      <div className="flex items-start gap-4">
        {/* Status Icon */}
        <div className={cn("mt-0.5 p-2 rounded-lg", status.bgColor)}>
          <StatusIcon className={cn("w-5 h-5", status.color)} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Badge
              variant="outline"
              className={cn("text-xs", taskType.color, taskType.bgColor)}>

              <TypeIcon className="w-3 h-3 mr-1" />
              {taskType.label}
            </Badge>
            <Flag className={cn("w-3.5 h-3.5", priority.flagColor)} />
            <span className="text-xs text-slate-500">{task.machineNo}</span>
          </div>

          <h3 className="font-medium text-white mb-1">{task.titleCn}</h3>

          <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
            <Folder className="w-3 h-3" />
            <span className="text-accent truncate">{task.projectName}</span>
          </div>

          {/* Progress bar */}
          <div className="mb-2">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-slate-400">进度</span>
              <span className="text-white">{task.progress}%</span>
            </div>
            <Progress value={task.progress} className="h-1.5" />
          </div>

          {/* Meta info */}
          <div className="flex items-center gap-4 text-xs text-slate-400">
            <span
              className={cn(
                "flex items-center gap-1",
                isOverdue ?
                "text-red-400" :
                daysUntilDue <= 3 ?
                "text-amber-400" :
                ""
              )}>

              <Calendar className="w-3 h-3" />
              {isOverdue ?
              `逾期 ${Math.abs(daysUntilDue)} 天` :
              daysUntilDue <= 3 && daysUntilDue >= 0 ?
              `剩余 ${daysUntilDue} 天` :
              task.plannedEnd}
            </span>
            <span className="flex items-center gap-1">
              <Timer className="w-3 h-3" />
              {task.actualHours}/{task.estimatedHours}h
            </span>
            {task.deliverables?.length > 0 &&
            <span className="flex items-center gap-1">
                <FileText className="w-3 h-3" />
                {task.deliverables?.length} 文件
            </span>
            }
          </div>

          {/* Blocked reason */}
          {task.blockedReason &&
          <div className="mt-2 p-2 rounded-lg bg-red-500/10 text-xs text-red-300 flex items-center gap-2">
              <AlertTriangle className="w-3 h-3" />
              {task.blockedReason}
          </div>
          }
        </div>

        {/* Arrow */}
        <ChevronRight className="w-5 h-5 text-slate-500" />
      </div>
    </motion.div>);

}
