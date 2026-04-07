/**
 * 任务卡片组件
 */




import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { taskStatuses, getPriorityStyle } from "./constants";

export default function TaskCard({ task, onClick }) {
  const priorityStyle = getPriorityStyle(task.priority);
  const statusConfig = (taskStatuses || []).find((s) => s.id === task.status);

  return (
    <motion.div
      variants={fadeIn}
      className="p-4 rounded-xl bg-surface-50/50 border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-all group"
      onClick={() => onClick(task)}>

      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <Badge className={cn("text-xs", task.typeColor)}>
              {task.typeName}
            </Badge>
            <Badge
              className={cn("text-xs", priorityStyle.bg, priorityStyle.text)}>

              {priorityStyle.label}
            </Badge>
            <Badge className={cn("text-xs", statusConfig?.color)}>
              {statusConfig?.name}
            </Badge>
          </div>
          <h4 className="text-sm font-medium text-white group-hover:text-primary transition-colors line-clamp-2">
            {task.title}
          </h4>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => e.stopPropagation()}>

              <MoreHorizontal className="w-4 h-4 text-slate-400" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>
              <Eye className="w-4 h-4 mr-2" />
              查看详情
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Edit className="w-4 h-4 mr-2" />
              编辑
            </DropdownMenuItem>
            <DropdownMenuItem className="text-red-400">
              <Trash2 className="w-4 h-4 mr-2" />
              删除
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <p className="text-xs text-slate-500 line-clamp-2 mb-3">
        {task.description}
      </p>

      <div className="flex items-center gap-3 text-xs text-slate-500 mb-3">
        <span className="flex items-center gap-1">
          <Building2 className="w-3 h-3" />
          {task.customer}
        </span>
        <span className="flex items-center gap-1">
          <Users className="w-3 h-3" />
          {task.source}
        </span>
      </div>

      {task.status !== "completed" && task.status !== "pending" &&
      <div className="space-y-1 mb-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">进度</span>
            <span className="text-white">{task.progress}%</span>
          </div>
          <Progress value={task.progress} className="h-1.5" />
      </div>
      }

      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-3 text-slate-500">
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {task.deadline}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {task.actualHours}/{task.estimatedHours}h
          </span>
        </div>
        {task.amount &&
        <span className="text-emerald-400">¥{task.amount}万</span>
        }
      </div>
    </motion.div>);

}
