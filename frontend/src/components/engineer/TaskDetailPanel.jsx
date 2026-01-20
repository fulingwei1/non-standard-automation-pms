/**
 * TaskDetailPanel Component - Slide-out panel for task details
 * Features: Task info, progress update, deliverables, BOM, review status
 */

import { useState } from "react";
import { motion } from "framer-motion";
import {
  X,
  Calendar,
  Clock,
  Timer,
  Flag,
  Folder,
  User,
  Users,
  FileText,
  Upload,
  Download,
  Eye,
  Send,
  MessageSquare,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Box,
  ClipboardCheck,
  MoreHorizontal,
  ExternalLink,
  ChevronRight,
  Target,
} from "lucide-react";
import { Button, Badge, Input, Progress, Card, CardContent, toast } from "../ui";
import { cn } from "../../lib/utils";

// Deliverable status config
const deliverableStatusConfig = {
  pending: { label: "待开始", color: "text-slate-400", bg: "bg-slate-500/10" },
  in_progress: {
    label: "进行中",
    color: "text-blue-400",
    bg: "bg-blue-500/10",
  },
  completed: {
    label: "已完成",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
  },
};

// Review status config
const reviewStatusConfig = {
  pending: { label: "待评审", color: "text-slate-400", bg: "bg-slate-500/10" },
  reviewing: {
    label: "评审中",
    color: "text-amber-400",
    bg: "bg-amber-500/10",
  },
  approved: {
    label: "已通过",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
  },
  rejected: { label: "已驳回", color: "text-red-400", bg: "bg-red-500/10" },
};

// Info Row Component
function InfoRow({ icon: Icon, label, value, className }) {
  const IconComponent = Icon;
  return (
    <div className={cn("flex items-center gap-3 text-sm", className)}>
      <IconComponent className="w-4 h-4 text-slate-500 flex-shrink-0" />
      <span className="text-slate-400 min-w-[60px]">{label}</span>
      <span className="text-white flex-1 truncate">{value}</span>
    </div>
  );
}

// Deliverable Item Component
function DeliverableItem({ item, onView, onDownload }) {
  const status = deliverableStatusConfig[item.status];

  return (
    <div className="flex items-center gap-3 p-2 rounded-lg bg-surface-2/50 hover:bg-surface-2 transition-colors">
      <FileText className="w-8 h-8 text-slate-400" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm text-white font-medium truncate">
            {item.name}
          </span>
          <Badge
            variant="outline"
            className={cn("text-[10px]", status.color, status.bg)}
          >
            {status.label}
          </Badge>
        </div>
        <div className="text-xs text-slate-500 flex items-center gap-2">
          <span>{item.type}</span>
          {item.size && <span>• {item.size}</span>}
        </div>
      </div>
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm" onClick={() => onView(item)}>
          <Eye className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={() => onDownload(item)}>
          <Download className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}

// Section Header Component
function SectionHeader({ icon: Icon, title, action }) {
  const IconComponent = Icon;
  return (
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-2">
        <IconComponent className="w-4 h-4 text-primary" />
        <h4 className="text-sm font-medium text-white">{title}</h4>
      </div>
      {action}
    </div>
  );
}

// Main TaskDetailPanel Component
export default function TaskDetailPanel({
  task,
  onClose,
  onUpdate,
  statusConfigs,
  priorityConfigs,
  taskTypeConfigs,
}) {
  const [progress, setProgress] = useState(task.progress);
  const [hours, setHours] = useState(task.actualHours);

  const status = statusConfigs[task.status];
  const priority = priorityConfigs[task.priority];
  const taskType = taskTypeConfigs[task.type];
  const reviewStatus = reviewStatusConfig[task.reviewStatus];
  const StatusIcon = status.icon;
  const TypeIcon = taskType.icon;

  const isOverdue =
    task.status !== "completed" && new Date(task.plannedEnd) < new Date();
  const daysUntilDue = Math.ceil(
    (new Date(task.plannedEnd) - new Date()) / (1000 * 60 * 60 * 24),
  );

  // Handle progress update
  const handleProgressUpdate = () => {
    onUpdate(task.id, { progress, actualHours: hours });
  };

  // Handle mark complete
  const handleMarkComplete = () => {
    onUpdate(task.id, { status: "completed", progress: 100 });
  };

  // Handle request review
  const handleRequestReview = () => {
    onUpdate(task.id, { reviewStatus: "reviewing" });
  };

  // Handle file view
  const getDeliverableUrl = (item) => {
    return (
      item?.url ||
      item?.file_url ||
      item?.fileUrl ||
      item?.download_url ||
      item?.downloadUrl ||
      item?.preview_url ||
      item?.previewUrl ||
      ""
    );
  };

  // Handle file view
  const handleFileView = (item) => {
    const url = getDeliverableUrl(item);
    if (!url) {
      toast.info("该交付物暂无可预览链接");
      return;
    }
    window.open(url, "_blank", "noopener,noreferrer");
  };

  // Handle file download
  const handleFileDownload = (item) => {
    const url = getDeliverableUrl(item);
    if (!url) {
      toast.info("该交付物暂无可下载链接");
      return;
    }

    const a = document.createElement("a");
    a.href = url;
    a.download = item?.name || "download";
    a.rel = "noopener noreferrer";
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  return (
    <motion.div
      initial={{ x: 400, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 400, opacity: 0 }}
      transition={{ type: "spring", damping: 25, stiffness: 200 }}
      className="fixed right-0 top-0 bottom-0 w-96 bg-surface-1 border-l border-border shadow-2xl overflow-y-auto z-50"
    >
      {/* Header */}
      <div className="sticky top-0 bg-surface-1 border-b border-border p-4 z-10">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Badge
                variant="outline"
                className={cn("text-xs", taskType.color, taskType.bgColor)}
              >
                <TypeIcon className="w-3 h-3 mr-1" />
                {taskType.label}
              </Badge>
              <Badge
                variant="outline"
                className={cn("text-xs", status.color, status.bgColor)}
              >
                <StatusIcon className="w-3 h-3 mr-1" />
                {status.label}
              </Badge>
            </div>
            <h3 className="text-lg font-semibold text-white mb-1">
              {task.titleCn}
            </h3>
            <p className="text-sm text-slate-400">{task.title}</p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-6">
        {/* Blocked Warning */}
        {task.blockedReason && (
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <span className="text-sm font-medium text-red-400">任务阻塞</span>
            </div>
            <p className="text-sm text-red-300 ml-6">{task.blockedReason}</p>
          </div>
        )}

        {/* Overdue Warning */}
        {isOverdue && !task.blockedReason && (
          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span className="text-sm font-medium text-amber-400">
                任务已逾期 {Math.abs(daysUntilDue)} 天
              </span>
            </div>
          </div>
        )}

        {/* Basic Info */}
        <div className="space-y-3">
          <SectionHeader icon={Box} title="基本信息" />
          <Card className="bg-surface-2/30">
            <CardContent className="p-3 space-y-2">
              <InfoRow icon={Folder} label="项目" value={task.projectName} />
              <InfoRow icon={Box} label="机台" value={task.machineNo} />
              <InfoRow icon={User} label="负责人" value={task.assignee} />
              <InfoRow icon={Users} label="审核人" value={task.reviewer} />
              <InfoRow
                icon={Flag}
                label="优先级"
                value={
                  <Badge
                    variant="outline"
                    className={cn("text-xs", priority.color)}
                  >
                    {priority.label}
                  </Badge>
                }
              />
            </CardContent>
          </Card>
        </div>

        {/* Schedule */}
        <div className="space-y-3">
          <SectionHeader icon={Calendar} title="进度安排" />
          <Card className="bg-surface-2/30">
            <CardContent className="p-3 space-y-2">
              <InfoRow
                icon={Calendar}
                label="计划开始"
                value={task.plannedStart}
              />
              <InfoRow
                icon={Calendar}
                label="计划结束"
                value={task.plannedEnd}
                className={
                  isOverdue
                    ? "text-red-400"
                    : daysUntilDue <= 3 && daysUntilDue >= 0
                      ? "text-amber-400"
                      : ""
                }
              />
              {task.actualStart && (
                <InfoRow
                  icon={Calendar}
                  label="实际开始"
                  value={task.actualStart}
                />
              )}
              <InfoRow
                icon={Timer}
                label="工时"
                value={`${task.actualHours}h / ${task.estimatedHours}h`}
              />
            </CardContent>
          </Card>
        </div>

        {/* Progress Update */}
        <div className="space-y-3">
          <SectionHeader icon={Target} title="进度更新" />
          <Card className="bg-surface-2/30">
            <CardContent className="p-3 space-y-4">
              {/* Progress Slider */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-slate-400">任务进度</span>
                  <span className="text-sm font-medium text-white">
                    {progress}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={progress}
                  onChange={(e) => setProgress(Number(e.target.value))}
                  className="w-full h-2 bg-surface-2 rounded-lg appearance-none cursor-pointer accent-primary"
                />
                <Progress value={progress} className="h-2 mt-2" />
              </div>

              {/* Hours Input */}
              <div>
                <label className="text-sm text-slate-400 mb-2 block">
                  实际工时
                </label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    value={hours}
                    onChange={(e) => setHours(Number(e.target.value))}
                    className="w-20"
                    min="0"
                    step="0.5"
                  />
                  <span className="text-sm text-slate-400">小时</span>
                  <span className="text-xs text-slate-500">
                    (预估 {task.estimatedHours}h)
                  </span>
                </div>
              </div>

              {/* Update Button */}
              <Button
                className="w-full"
                onClick={handleProgressUpdate}
                disabled={
                  progress === task.progress && hours === task.actualHours
                }
              >
                <CheckCircle2 className="w-4 h-4 mr-1" />
                更新进度
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Deliverables */}
        <div className="space-y-3">
          <SectionHeader
            icon={FileText}
            title="设计交付物"
            action={
              <Button variant="ghost" size="sm">
                <Upload className="w-4 h-4 mr-1" />
                上传
              </Button>
            }
          />
          <div className="space-y-2">
            {task.deliverables.length > 0 ? (
              task.deliverables.map((item) => (
                <DeliverableItem
                  key={item.id}
                  item={item}
                  onView={handleFileView}
                  onDownload={handleFileDownload}
                />
              ))
            ) : (
              <div className="text-center py-6 text-slate-500 text-sm">
                暂无交付物
              </div>
            )}
          </div>
        </div>

        {/* BOM */}
        {task.bomItems > 0 && (
          <div className="space-y-3">
            <SectionHeader icon={Layers} title="BOM关联" />
            <Card className="bg-surface-2/30 cursor-pointer hover:bg-surface-2/50 transition-colors">
              <CardContent className="p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Layers className="w-8 h-8 text-amber-400" />
                    <div>
                      <p className="text-sm font-medium text-white">物料清单</p>
                      <p className="text-xs text-slate-400">
                        {task.bomItems} 项物料
                      </p>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-slate-500" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Milestone */}
        {task.milestone && (
          <div className="space-y-3">
            <SectionHeader icon={Flag} title="关联里程碑" />
            <Card className="bg-purple-500/5 border-purple-500/20">
              <CardContent className="p-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
                    <Flag className="w-4 h-4 text-purple-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-purple-300">
                      {task.milestone}
                    </p>
                    <p className="text-xs text-purple-400/70">
                      {task.milestoneDate}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Review Status */}
        <div className="space-y-3">
          <SectionHeader icon={ClipboardCheck} title="评审状态" />
          <Card className="bg-surface-2/30">
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-xs",
                      reviewStatus.color,
                      reviewStatus.bg,
                    )}
                  >
                    {reviewStatus.label}
                  </Badge>
                  {task.reviewer && (
                    <span className="text-xs text-slate-500">
                      评审人: {task.reviewer}
                    </span>
                  )}
                </div>
                {task.reviewStatus === "pending" && task.progress >= 80 && (
                  <Button size="sm" onClick={handleRequestReview}>
                    <Send className="w-4 h-4 mr-1" />
                    申请评审
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Notes */}
        {task.notes && (
          <div className="space-y-3">
            <SectionHeader icon={MessageSquare} title="备注" />
            <Card className="bg-surface-2/30">
              <CardContent className="p-3">
                <p className="text-sm text-slate-300">{task.notes}</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Dependencies */}
        {task.dependencies.length > 0 && (
          <div className="space-y-3">
            <SectionHeader icon={ExternalLink} title="前置任务" />
            <Card className="bg-surface-2/30">
              <CardContent className="p-3">
                <div className="text-sm text-slate-400">
                  依赖 {task.dependencies.length} 个前置任务
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="sticky bottom-0 bg-surface-1 border-t border-border p-4 space-y-2">
        {task.status !== "completed" && (
          <Button
            variant="outline"
            className="w-full"
            onClick={handleMarkComplete}
          >
            <CheckCircle2 className="w-4 h-4 mr-1" />
            标记为完成
          </Button>
        )}
        <div className="flex gap-2">
          <Button variant="ghost" className="flex-1">
            <AlertTriangle className="w-4 h-4 mr-1" />
            报告阻塞
          </Button>
          <Button variant="ghost" className="flex-1">
            <MessageSquare className="w-4 h-4 mr-1" />
            添加备注
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
