import { motion } from "framer-motion";
import {
  Calendar,
  Clock,
  CheckCircle2,
  Target,
  TrendingUp,
  ArrowRight,
} from "lucide-react";
import { cn } from "../../lib/utils";
import {
  getStatusBadge,
  getTypeBadge,
  getUrgencyColor,
} from "../../utils/evaluationTaskUtils";

/**
 * 评价任务项组件
 */
export const TaskItem = ({ task, index, onEvaluate }) => {
  const statusBadge = getStatusBadge(task.status);
  const typeBadge = getTypeBadge(
    task.evaluationType || task.evaluator_type,
    task.projectName || task.project_name,
  );
  const urgencyColor = getUrgencyColor(task.daysLeft || task.days_left || 0);
  const employeeName = task.employeeName || task.employee_name || "未知";
  const daysLeft = task.daysLeft || task.days_left || 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 hover:border-slate-600 transition-all overflow-hidden"
    >
      <div className="p-6">
        {/* 任务头部 */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-4">
            {/* 员工头像 */}
            <div className="h-12 w-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold text-lg">
                {employeeName.charAt(0)}
              </span>
            </div>

            {/* 员工信息 */}
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="text-xl font-bold text-white">{employeeName}</h3>
                <span
                  className={cn(
                    "px-3 py-1 rounded-full text-sm font-medium",
                    statusBadge.color,
                  )}
                >
                  {statusBadge.label}
                </span>
                <span
                  className={cn(
                    "px-3 py-1 rounded-full text-sm font-medium",
                    typeBadge.color,
                  )}
                >
                  {typeBadge.label}
                </span>
              </div>

              <div className="flex items-center gap-4 text-sm text-slate-400">
                <span>
                  {task.department || task.employee_department || "-"}
                </span>
                <span>·</span>
                <span>{task.position || task.employee_position || "-"}</span>
                <span>·</span>
                <span>权重 {task.weight || task.project_weight || 50}%</span>
              </div>
            </div>
          </div>

          {/* 评分结果 */}
          {task.status === "COMPLETED" && task.score !== null && (
            <div className="text-right">
              <p className="text-sm text-slate-400 mb-1">评分</p>
              <p className="text-3xl font-bold text-emerald-400">
                {task.score}
              </p>
            </div>
          )}
        </div>

        {/* 工作总结预览 */}
        {(task.workSummary || task.summary) && (
          <div className="bg-slate-900/30 rounded-lg p-4 mb-4">
            <div className="flex items-center gap-2 text-slate-400 mb-3">
              <Target className="h-4 w-4" />
              <span className="text-sm font-medium">工作总结</span>
            </div>
            <p className="text-slate-300 line-clamp-2 mb-2">
              {task.workSummary?.workContent ||
                task.workSummary?.work_content ||
                task.summary?.work_content ||
                "暂无工作总结"}
            </p>
            {(task.workSummary?.highlights || task.summary?.highlights) && (
              <div className="flex items-start gap-2 mt-2 p-2 bg-amber-500/10 rounded border border-amber-500/20">
                <TrendingUp className="h-4 w-4 text-amber-400 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-amber-300 line-clamp-1">
                  {task.workSummary?.highlights || task.summary?.highlights}
                </p>
              </div>
            )}
          </div>
        )}

        {/* 评价内容（已完成）*/}
        {task.status === "COMPLETED" && task.comment && (
          <div className="bg-emerald-500/10 rounded-lg p-4 mb-4 border border-emerald-500/20">
            <div className="flex items-center gap-2 text-emerald-400 mb-2">
              <CheckCircle2 className="h-4 w-4" />
              <span className="text-sm font-medium">评价意见</span>
            </div>
            <p className="text-slate-300">{task.comment}</p>
          </div>
        )}

        {/* 底部操作栏 */}
        <div className="flex items-center justify-between pt-4 border-t border-slate-700/50">
          <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2 text-slate-400">
              <Calendar className="h-4 w-4" />
              <span>提交: {task.submitDate || task.submit_date || "-"}</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className={cn("h-4 w-4", urgencyColor)} />
              <span className={urgencyColor}>
                {daysLeft < 0
                  ? `已过期 ${Math.abs(daysLeft)} 天`
                  : daysLeft === 0
                    ? "今天截止"
                    : `剩余 ${daysLeft} 天`}
              </span>
            </div>
          </div>

          {task.status === "PENDING" && (
            <button
              onClick={() => onEvaluate(task)}
              className="px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-lg font-medium transition-all flex items-center gap-2"
            >
              开始评价
              <ArrowRight className="h-4 w-4" />
            </button>
          )}

          {task.status === "COMPLETED" && (
            <button
              onClick={() => onEvaluate(task)}
              className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              查看详情
              <ArrowRight className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
};
