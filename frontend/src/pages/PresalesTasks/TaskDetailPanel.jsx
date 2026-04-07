/**
 * 任务详情面板
 */
import { useState } from "react";


import { cn } from "../../lib/utils";
import { presaleApi } from "../../services/api";
import { taskStatuses, getPriorityStyle } from "./constants";

export default function TaskDetailPanel({ task, onClose, onUpdate }) {
  const [progress, setProgress] = useState(task?.progress || 0);
  const [progressNote, setProgressNote] = useState("");
  const [actualHours, setActualHours] = useState(task?.actualHours || 0);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isCompleting, setIsCompleting] = useState(false);
  const [isAccepting, setIsAccepting] = useState(false);

  if (!task) {return null;}

  const priorityStyle = getPriorityStyle(task.priority);
  const statusConfig = (taskStatuses || []).find((s) => s.id === task.status);

  // 接单
  const handleAccept = async () => {
    try {
      setIsAccepting(true);
      await presaleApi.tickets.accept(task.ticketId, {});
      alert("接单成功！");
      onUpdate?.();
      onClose();
    } catch (err) {
      console.error("Failed to accept ticket:", err);
      alert(
        "接单失败：" + (
        err.response?.data?.detail || err.message || "未知错误")
      );
    } finally {
      setIsAccepting(false);
    }
  };

  // 更新进度
  const handleUpdateProgress = async () => {
    try {
      setIsUpdating(true);
      await presaleApi.tickets.updateProgress(task.ticketId, {
        progress_percent: progress,
        progress_note: progressNote
      });
      alert("进度已更新！");
      onUpdate?.();
      setProgressNote("");
    } catch (err) {
      console.error("Failed to update progress:", err);
      alert(
        "更新失败：" + (
        err.response?.data?.detail || err.message || "未知错误")
      );
    } finally {
      setIsUpdating(false);
    }
  };

  // 完成工单
  const handleComplete = async () => {
    if (!actualHours || actualHours <= 0) {
      alert("请输入实际工时");
      return;
    }

    try {
      setIsCompleting(true);
      await presaleApi.tickets.complete(task.ticketId, {
        actual_hours: actualHours
      });
      alert("工单已完成！");
      onUpdate?.();
      onClose();
    } catch (err) {
      console.error("Failed to complete ticket:", err);
      alert(
        "完成失败：" + (
        err.response?.data?.detail || err.message || "未知错误")
      );
    } finally {
      setIsCompleting(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className="fixed right-0 top-0 h-full w-full md:w-[450px] bg-surface-100/95 backdrop-blur-xl border-l border-white/5 shadow-2xl z-50 flex flex-col">

        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/5">
          <h2 className="text-lg font-semibold text-white">任务详情</h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5 text-slate-400" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-6">
          {/* Title and badges */}
          <div>
            <div className="flex items-center gap-2 mb-2 flex-wrap">
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
            <h3 className="text-xl font-semibold text-white">{task.title}</h3>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-slate-400">任务描述</h4>
            <p className="text-sm text-white bg-surface-50 p-3 rounded-lg">
              {task.description}
            </p>
          </div>

          {/* Basic Info */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-400">基本信息</h4>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">客户</p>
                <p className="text-sm text-white flex items-center gap-1">
                  <Building2 className="w-3 h-3 text-primary" />
                  {task.customer}
                </p>
              </div>
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">来源</p>
                <p className="text-sm text-white flex items-center gap-1">
                  <Users className="w-3 h-3 text-primary" />
                  {task.source}
                </p>
              </div>
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">负责人</p>
                <p className="text-sm text-white flex items-center gap-1">
                  <User className="w-3 h-3 text-primary" />
                  {task.assignee}
                </p>
              </div>
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">关联商机</p>
                <p className="text-sm text-white flex items-center gap-1">
                  <Briefcase className="w-3 h-3 text-primary" />
                  {task.opportunity}
                </p>
              </div>
            </div>
          </div>

          {/* Timeline */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-400">时间信息</h4>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">创建时间</p>
                <p className="text-sm text-white">{task.createdAt}</p>
              </div>
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">截止时间</p>
                <p className="text-sm text-white">{task.deadline}</p>
              </div>
            </div>
          </div>

          {/* Progress */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-400">进度 & 工时</h4>
            <div className="bg-surface-50 p-4 rounded-lg space-y-3">
              <div className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">完成进度</span>
                  <span className="text-white">{progress}%</span>
                </div>
                <Progress value={progress || "unknown"} className="h-2" />
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">工时</span>
                <span className="text-white">
                  {actualHours}h / {task.estimatedHours || 0}h
                </span>
              </div>
              {task.estimatedHours > 0 &&
              <Progress
                value={actualHours / task.estimatedHours * 100}
                className="h-2" />

              }
            </div>
          </div>

          {/* Deliverables */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-400">交付物</h4>
            <div className="space-y-2">
              {(task.deliverables || []).map((item, index) =>
              <div
                key={index}
                className="flex items-center gap-2 bg-surface-50 p-3 rounded-lg">

                  <FileText className="w-4 h-4 text-slate-500" />
                  <span className="text-sm text-white">{item}</span>
                  {task.status === "completed" &&
                <CheckCircle className="w-4 h-4 text-emerald-500 ml-auto" />
                }
              </div>
              )}
            </div>
          </div>

          {/* Amount */}
          {task.amount &&
          <div className="bg-gradient-to-r from-emerald-500/10 to-teal-500/10 p-4 rounded-lg border border-emerald-500/20">
              <p className="text-xs text-slate-400 mb-1">关联金额</p>
              <p className="text-2xl font-bold text-emerald-400">
                ¥{task.amount}万
              </p>
          </div>
          }
        </div>

        {/* 操作区域 */}
        {task.status === "pending" &&
        <div className="p-4 border-t border-white/5">
            <Button
            onClick={handleAccept}
            disabled={isAccepting}
            className="w-full">

              <CheckCircle className="w-4 h-4 mr-2" />
              {isAccepting ? "接单中..." : "接单处理"}
            </Button>
        </div>
        }

        {(task.status === "in_progress" || task.status === "reviewing") &&
        <div className="p-4 border-t border-white/5 space-y-3">
            <div className="space-y-2">
              <label className="text-sm text-slate-400">更新进度</label>
              <div className="flex items-center gap-3">
                <Input
                type="number"
                min="0"
                max="100"
                value={progress || "unknown"}
                onChange={(e) => setProgress(parseInt(e.target.value) || 0)}
                className="flex-1" />

                <span className="text-sm text-slate-400">%</span>
              </div>
              <Progress value={progress || "unknown"} className="h-2" />
              <Input
              type="text"
              placeholder="进度说明..."
              value={progressNote || "unknown"}
              onChange={(e) => setProgressNote(e.target.value)}
              className="w-full" />

              <Button
              onClick={handleUpdateProgress}
              disabled={isUpdating}
              variant="outline"
              className="w-full">

                <Clock className="w-4 h-4 mr-2" />
                {isUpdating ? "更新中..." : "更新进度"}
              </Button>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">实际工时（小时）</label>
              <Input
              type="number"
              min="0"
              value={actualHours || "unknown"}
              onChange={(e) =>
              setActualHours(parseFloat(e.target.value) || 0)
              }
              className="w-full" />

              <Button
              onClick={handleComplete}
              disabled={isCompleting || !actualHours || actualHours <= 0}
              className="w-full">

                <CheckCircle className="w-4 h-4 mr-2" />
                {isCompleting ? "完成中..." : "完成工单"}
              </Button>
            </div>
        </div>
        }

        {/* Footer */}
        <div className="p-4 border-t border-white/5 flex gap-2">
          <Button variant="outline" className="flex-1" onClick={onClose}>
            <X className="w-4 h-4 mr-2" />
            关闭
          </Button>
        </div>
      </motion.div>
    </AnimatePresence>);

}
