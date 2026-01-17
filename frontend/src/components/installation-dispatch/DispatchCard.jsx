/**
 * DispatchCard Component
 * 安装任务卡片组件
 */

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Badge,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
  Textarea,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../../components/ui";
import {
  Plus,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Flag,
  User,
  Calendar,
  MapPin,
  Phone,
  Mail,
  Edit,
  Play,
  Pause,
  Square,
  Trash2,
  MoreVertical } from
"lucide-react";
import { cn } from "../../lib/utils";
import {
  taskStatusConfigs,
  priorityConfigs,
  installationTypeConfigs,
  roleConfigs as _roleConfigs,
  formatDate,
  formatDuration,
  isTaskOverdue } from
"./installationDispatchConstants";import { toast } from "sonner";

export function DispatchCard({
  task,
  onUpdateTask,
  onDeleteTask,
  onStartTask,
  onPauseTask,
  onCompleteTask,
  onEngineerAssignment,
  currentUser,
  showActions = true,
  compact = false,
  className = ""
}) {
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [assignForm, setAssignForm] = useState({
    engineer_id: "",
    scheduled_date: "",
    notes: ""
  });

  const statusConfig = taskStatusConfigs[task.status] || taskStatusConfigs.SCHEDULED;
  const priorityConfig = priorityConfigs[task.priority] || priorityConfigs.NORMAL;
  const installationTypeConfig = installationTypeConfigs[task.installation_type] || installationTypeConfigs.INSTALLATION;

  const progress = calculateProgress(task);

  const canEdit = currentUser?.id === task.assigned_engineer ||
  currentUser?.id === task.created_by ||
  currentUser?.permissions?.includes("installation:manage");

  const canAssign = currentUser?.permissions?.includes("installation:dispatch") ||
  currentUser?.permissions?.includes("installation:assign");

  const canDelete = currentUser?.id === task.created_by ||
  currentUser?.permissions?.includes("installation:manage");

  const canStart = task.status === "SCHEDULED" && task.assigned_engineer;
  const canPause = task.status === "IN_PROGRESS";
  const canComplete = task.status === "IN_PROGRESS" && task.progress >= 100;

  const isOverdue = isTaskOverdue(task.status, task.planned_end_date);

  function calculateProgress(task) {
    if (task.status === "COMPLETED") return 100;
    if (task.status === "CANCELLED") return 0;
    if (task.progress !== undefined) return task.progress;

    if (!task.start_date || !task.end_date) return 0;

    const now = new Date();
    const start = new Date(task.start_date);
    const end = new Date(task.end_date);

    if (now < start) return 0;
    if (now > end) return 100;

    const total = end - start;
    const elapsed = now - start;
    return Math.round(elapsed / total * 100);
  }

  const handleEngineerAssignment = () => {
    if (!assignForm.engineer_id) {
      toast.warning("请选择工程师");
      return;
    }

    onEngineerAssignment({
      ...task,
      assigned_engineer_id: assignForm.engineer_id,
      scheduled_date: assignForm.scheduled_date,
      notes: assignForm.notes
    });

    setAssignForm({
      engineer_id: "",
      scheduled_date: "",
      notes: ""
    });
    setShowAssignDialog(false);
  };

  const _handleUpdateStatus = (newStatus) => {
    onUpdateTask({
      ...task,
      status: newStatus,
      updated_at: new Date().toISOString()
    });
  };

  const handleDelete = () => {
    if (window.confirm("确定要删除这个任务吗？")) {
      onDeleteTask(task.id);
    }
  };

  if (compact) {
    return (
      <motion.div
        whileHover={{ scale: 1.02 }}
        className={cn(
          "p-3 rounded-lg cursor-pointer border-l-4 bg-slate-800/50 hover:bg-slate-800/70 transition-all",
          statusConfig.borderColor,
          isOverdue && "ring-1 ring-red-500",
          className
        )}
        onClick={() => setShowDetailDialog(true)}>

        <div className="flex items-center gap-2 mb-1">
          <div className="w-6 h-6 rounded-full bg-slate-700 flex items-center justify-center">
            {installationTypeConfig.icon}
          </div>
          <h4 className="text-sm font-medium text-white truncate flex-1">
            {task.title}
          </h4>
          <div className="flex items-center gap-1">
            <Badge
              variant="outline"
              className={cn(
                priorityConfig.bg,
                priorityConfig.borderColor,
                "text-xs"
              )}>

              {priorityConfig.label}
            </Badge>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs text-slate-400">
          <div className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            <span>{formatDate(task.scheduled_date)}</span>
          </div>
          {task.location &&
          <div className="flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              <span>{task.location}</span>
            </div>
          }
        </div>

        {progress !== undefined &&
        <div className="mt-2">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs text-slate-400">进度</span>
              <span className="text-xs text-white">{progress}%</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-1">
              <div
              className={cn(
                "h-1 rounded-full transition-all",
                getProgressColor(progress)
              )}
              style={{ width: `${progress}%` }}>

              </div>
            </div>
          </div>
        }
      </motion.div>);

  }

  return (
    <>
      {/* Card Component */}
      <motion.div
        whileHover={{ scale: 1.02 }}
        className={cn(
          "bg-slate-800/50 border rounded-lg hover:bg-slate-800/70 transition-colors cursor-pointer",
          statusConfig.borderColor,
          isOverdue && "ring-1 ring-red-500",
          className
        )}
        onClick={() => setShowDetailDialog(true)}>

        <CardHeader className="p-4 pb-2">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3 flex-1">
              <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0">
                {installationTypeConfig.icon}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <CardTitle className="text-lg font-medium text-white truncate">
                    {task.title}
                  </CardTitle>
                  <Badge className={cn(
                    statusConfig.color,
                    statusConfig.textColor,
                    "text-xs"
                  )}>
                    {statusConfig.label}
                  </Badge>
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                  <Badge className={cn(
                    priorityConfig.bg,
                    priorityConfig.borderColor,
                    "text-xs"
                  )}>
                    {priorityConfig.label}
                  </Badge>

                  {task.installation_type &&
                  <Badge variant="outline" className="text-xs">
                      {installationTypeConfig.label}
                    </Badge>
                  }

                  {task.project_name &&
                  <Badge variant="outline" className="text-xs">
                      项目: {task.project_name}
                    </Badge>
                  }
                </div>
              </div>
            </div>

            {showActions && canEdit &&
            <div className="flex items-center gap-2">
                <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowEditDialog(true);
                }}>

                  <Edit className="w-4 h-4" />
                </Button>

                {canAssign &&
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowAssignDialog(true);
                }}>

                    <User className="w-4 h-4" />
                  </Button>
              }

                {canDelete &&
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDelete();
                }}>

                    <Trash2 className="w-4 h-4" />
                  </Button>
              }
              </div>
            }
          </div>
        </CardHeader>

        <CardContent className="p-4 pt-0 space-y-3">
          {/* 任务信息 */}
          {task.description &&
          <p className="text-sm text-slate-300 line-clamp-2">
              {task.description}
            </p>
          }

          {/* 时间信息 */}
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="flex items-center gap-1 text-slate-400">
              <Calendar className="w-3 h-3" />
              <span>安排: {formatDate(task.scheduled_date)}</span>
            </div>
            <div className="flex items-center gap-1 text-slate-400">
              <Clock className="w-3 h-3" />
              <span>预计: {formatDuration(task.estimated_duration)}</span>
            </div>
          </div>

          {/* 位置信息 */}
          {task.location &&
          <div className="flex items-center gap-1 text-xs text-slate-400">
              <MapPin className="w-3 h-3" />
              <span>{task.location}</span>
            </div>
          }

          {/* 负责人信息 */}
          {task.assigned_engineer_name &&
          <div className="flex items-center gap-1 text-xs text-slate-400">
              <User className="w-3 h-3" />
              <span>负责人: {task.assigned_engineer_name}</span>
            </div>
          }

          {/* 联系信息 */}
          {(task.contact_phone || task.contact_email) &&
          <div className="flex items-center gap-3 text-xs">
              {task.contact_phone &&
            <div className="flex items-center gap-1 text-slate-400">
                  <Phone className="w-3 h-3" />
                  <span>{task.contact_phone}</span>
                </div>
            }
              {task.contact_email &&
            <div className="flex items-center gap-1 text-slate-400">
                  <Mail className="w-3 h-3" />
                  <span>{task.contact_email}</span>
                </div>
            }
            </div>
          }

          {/* 进度条 */}
          {progress !== undefined &&
          <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs text-slate-400">进度</span>
                <span className="text-xs text-white">{progress}%</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-1.5">
                <div
                className={cn(
                  "h-1.5 rounded-full transition-all",
                  getProgressColor(progress)
                )}
                style={{ width: `${progress}%` }}>

                </div>
              </div>
            </div>
          }

          {/* 状态操作按钮 */}
          {showActions && canEdit &&
          <div className="flex items-center gap-2 pt-2 border-t border-slate-700">
              {canStart &&
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onStartTask(task.id);
              }}>

                  <Play className="w-3 h-3 mr-1" />
                  开始
                </Button>
            }

              {canPause &&
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onPauseTask(task.id);
              }}>

                  <Pause className="w-3 h-3 mr-1" />
                  暂停
                </Button>
            }

              {canComplete &&
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onCompleteTask(task.id);
              }}>

                  <Square className="w-3 h-3 mr-1" />
                  完成
                </Button>
            }
            </div>
          }
        </CardContent>
      </motion.div>

      {/* 任务详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{task.title}</DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-slate-400">任务状态</label>
                <Badge className={cn(
                  statusConfig.color,
                  statusConfig.textColor,
                  "mt-1"
                )}>
                  {statusConfig.label}
                </Badge>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-400">优先级</label>
                <Badge className={cn(
                  priorityConfig.bg,
                  priorityConfig.borderColor,
                  "mt-1"
                )}>
                  {priorityConfig.label}
                </Badge>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-400">任务描述</label>
              <p className="mt-1 text-sm text-slate-300">
                {task.description || "暂无描述"}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-slate-400">安装类型</label>
                <p className="mt-1 text-sm text-slate-300">
                  {installationTypeConfig.label}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-400">预计时长</label>
                <p className="mt-1 text-sm text-slate-300">
                  {formatDuration(task.estimated_duration)}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-slate-400">安排日期</label>
                <p className="mt-1 text-sm text-slate-300">
                  {formatDate(task.scheduled_date)}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-400">项目</label>
                <p className="mt-1 text-sm text-slate-300">
                  {task.project_name || "未分配"}
                </p>
              </div>
            </div>

            {task.location &&
            <div>
                <label className="text-sm font-medium text-slate-400">安装地点</label>
                <p className="mt-1 text-sm text-slate-300">
                  {task.location}
                </p>
              </div>
            }

            {(task.contact_phone || task.contact_email) &&
            <div>
                <label className="text-sm font-medium text-slate-400">联系方式</label>
                <div className="mt-1 space-y-1 text-sm text-slate-300">
                  {task.contact_phone &&
                <p>电话: {task.contact_phone}</p>
                }
                  {task.contact_email &&
                <p>邮箱: {task.contact_email}</p>
                }
                </div>
              </div>
            }

            {task.assigned_engineer_name &&
            <div>
                <label className="text-sm font-medium text-slate-400">负责人</label>
                <p className="mt-1 text-sm text-slate-300">
                  {task.assigned_engineer_name}
                  {task.assigned_engineer_contact &&
                <span className="ml-2 text-slate-400">
                      ({task.assigned_engineer_contact})
                    </span>
                }
                </p>
              </div>
            }
          </DialogBody>
          <DialogFooter>
            {showActions && canEdit &&
            <>
                {canStart &&
              <Button
                variant="outline"
                onClick={() => {
                  onStartTask(task.id);
                  setShowDetailDialog(false);
                }}>

                    <Play className="w-4 h-4 mr-1" />
                    开始任务
                  </Button>
              }

                {canComplete &&
              <Button
                onClick={() => {
                  onCompleteTask(task.id);
                  setShowDetailDialog(false);
                }}>

                    <CheckCircle2 className="w-4 h-4 mr-1" />
                    完成任务
                  </Button>
              }
              </>
            }
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 编辑任务对话框 */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>编辑任务</DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">任务标题</label>
              <Input
                value={task.title}
                onChange={(_e) => {

                  // This would be handled by form state management
                }} placeholder="任务标题" />

            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">任务描述</label>
              <Textarea
                value={task.description}
                onChange={(_e) => {

                  // This would be handled by form state management
                }} placeholder="任务描述"
                rows={4} />

            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">优先级</label>
                <Select value={task.priority} onValueChange={(_value) => {

                  // This would be handled by form state management
                }}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(priorityConfigs).map(([key, config]) => <SelectItem key={key} value={key}>
                        {config.label}
                      </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">预计时长（小时）</label>
                <Input
                  type="number"
                  value={task.estimated_duration}
                  onChange={(_e) => {

                    // This would be handled by form state management
                  }} placeholder="0" />

              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">安排日期</label>
                <Input
                  type="date"
                  value={task.scheduled_date}
                  onChange={(_e) => {

                    // This would be handled by form state management
                  }} />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">安装地点</label>
                <Input
                  value={task.location}
                  onChange={(_e) => {

                    // This would be handled by form state management
                  }} placeholder="安装地点" />

              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              取消
            </Button>
            <Button onClick={() => {
              // Handle form submission
              setShowEditDialog(false);
            }}>
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 分配工程师对话框 */}
      <Dialog open={showAssignDialog} onOpenChange={setShowAssignDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>分配工程师</DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">选择工程师 *</label>
              <Select
                value={assignForm.engineer_id}
                onValueChange={(value) =>
                setAssignForm({ ...assignForm, engineer_id: value })
                }>

                <SelectTrigger>
                  <SelectValue placeholder="选择工程师" />
                </SelectTrigger>
                <SelectContent>
                  {/* This would be populated with engineer list */}
                  <SelectItem value="eng1">张工程师</SelectItem>
                  <SelectItem value="eng2">李工程师</SelectItem>
                  <SelectItem value="eng3">王工程师</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">重新安排日期</label>
              <Input
                type="date"
                value={assignForm.scheduled_date}
                onChange={(e) =>
                setAssignForm({ ...assignForm, scheduled_date: e.target.value })
                } />

            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">备注</label>
              <Textarea
                value={assignForm.notes}
                onChange={(e) =>
                setAssignForm({ ...assignForm, notes: e.target.value })
                }
                placeholder="分配备注"
                rows={3} />

            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowAssignDialog(false)}>

              取消
            </Button>
            <Button onClick={handleEngineerAssignment}>确认分配</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>);

}

function getProgressColor(progress) {
  if (progress === 100) return "bg-green-500";
  if (progress >= 75) return "bg-blue-500";
  if (progress >= 50) return "bg-yellow-500";
  if (progress >= 25) return "bg-orange-500";
  return "bg-red-500";
}