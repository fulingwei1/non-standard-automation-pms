/**
 * ECN Task Board Component
 * ECN 执行任务看板组件
 */

import { useState } from "react";
import { Badge } from "../../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../../components/ui/dialog";
import { Input } from "../../components/ui/input";
import { Textarea } from "../../components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../../components/ui/select";
import {
  Plus,
  Clock,
  CheckCircle2,
  AlertTriangle,
  User,
  Calendar,
  Flag } from
"lucide-react";
import {
  taskTypeConfigs,
  taskStatusConfigs,
  formatStatus as _formatStatus } from
"@/lib/constants/ecn";
import { cn, formatDate } from "../../lib/utils";import { toast } from "sonner";

export function ECNTaskBoard({
  tasks,
  ecn,
  onCreateTask,
  onUpdateTask: _onUpdateTask,
  currentUser,
  loading: _loading
}) {
  const [showTaskDialog, setShowTaskDialog] = useState(false);
  const [taskForm, setTaskForm] = useState({
    task_name: "",
    task_type: "",
    task_dept: "",
    task_description: "",
    planned_start: "",
    planned_end: "",
    assignee_id: ""
  });

  const _taskStatuses = ["PENDING", "IN_PROGRESS", "COMPLETED", "DELAYED"];
  const statusColumns = {
    PENDING: { title: "待开始", icon: <Clock className="w-4 h-4" />, color: "border-slate-600" },
    IN_PROGRESS: { title: "进行中", icon: <div className="w-4 h-4 bg-blue-500 rounded-full animate-pulse" />, color: "border-blue-600" },
    COMPLETED: { title: "已完成", icon: <CheckCircle2 className="w-4 h-4 text-green-500" />, color: "border-green-600" },
    DELAYED: { title: "已延期", icon: <AlertTriangle className="w-4 h-4 text-red-500" />, color: "border-red-600" }
  };

  const getTasksByStatus = (status) => {
    return (tasks || []).filter((task) => task.status === status);
  };

  const handleCreateTask = () => {
    if (!taskForm.task_name || !taskForm.task_type || !taskForm.task_dept) {
      toast.warning("请填写必填字段");
      return;
    }

    onCreateTask({
      ...taskForm,
      ecn_id: ecn.id,
      created_by: currentUser.id,
      created_time: new Date().toISOString()
    });

    setTaskForm({
      task_name: "",
      task_type: "",
      task_dept: "",
      task_description: "",
      planned_start: "",
      planned_end: "",
      assignee_id: ""
    });
    setShowTaskDialog(false);
  };

  const getTaskPriority = (task) => {
    const now = new Date();
    const endDate = new Date(task.planned_end);
    const daysLeft = Math.ceil((endDate - now) / (1000 * 60 * 60 * 24));

    if (daysLeft < 0) {return { label: "延期", color: "bg-red-500" };}
    if (daysLeft <= 3) {return { label: "紧急", color: "bg-orange-500" };}
    if (daysLeft <= 7) {return { label: "中等", color: "bg-yellow-500" };}
    return { label: "正常", color: "bg-green-500" };
  };

  const canCreateTask = () => {
    return (ecn.status === "APPROVED" || ecn.status === "EXECUTING") && currentUser;
  };

  return (
    <>
      <div className="flex justify-end gap-2 mb-4">
        {canCreateTask() &&
        <Button onClick={() => setShowTaskDialog(true)}>
            <Plus className="w-4 h-4 mr-2" />
            创建任务
        </Button>
        }
      </div>

      <div className="grid grid-cols-4 gap-4">
        {Object.entries(statusColumns).map(([status, column]) =>
        <div key={status} className={`border-2 ${column.color} rounded-lg bg-slate-800/30`}>
            <div className="p-4 border-b border-slate-700">
              <div className="flex items-center gap-2">
                {column.icon}
                <h3 className="font-semibold text-white">{column.title}</h3>
                <Badge variant="outline" className="ml-auto text-xs">
                  {getTasksByStatus(status).length}
                </Badge>
              </div>
            </div>
            
            <div className="p-2 space-y-2 max-h-[600px] overflow-y-auto">
              {getTasksByStatus(status).map((task) => {
              const priority = getTaskPriority(task);
              const taskTypeConfig = taskTypeConfigs[task.task_type] || taskTypeConfigs.OTHER;
              const _taskStatusConfig = taskStatusConfigs[task.status];

              return (
                <Card key={task.id} className="bg-slate-900/50 border-slate-700 hover:bg-slate-900/70 transition-colors">
                    <CardContent className="p-3">
                      <div className="space-y-2">
                        <div className="flex justify-between items-start gap-2">
                          <h4 className="text-sm font-medium text-white line-clamp-2">
                            {task.task_name}
                          </h4>
                          <Badge className={cn(priority.color, "text-xs text-white")}>
                            {priority.label}
                          </Badge>
                        </div>

                        <div className="flex items-center gap-1">
                          <Badge className={cn(
                          taskTypeConfig.color,
                          taskTypeConfig.textColor,
                          "text-xs"
                        )}>
                            {taskTypeConfig.label}
                          </Badge>
                          {task.task_dept &&
                        <Badge variant="outline" className="text-xs">
                              {task.task_dept}
                        </Badge>
                        }
                        </div>

                        {task.assignee_name &&
                      <div className="flex items-center gap-1 text-xs text-slate-400">
                            <User className="w-3 h-3" />
                            {task.assignee_name}
                      </div>
                      }

                        {task.planned_end &&
                      <div className="flex items-center gap-1 text-xs text-slate-400">
                            <Calendar className="w-3 h-3" />
                            截止: {formatDate(task.planned_end)}
                      </div>
                      }

                        {task.progress !== undefined &&
                      <div className="mt-2">
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-xs text-slate-400">进度</span>
                              <span className="text-xs text-white">{task.progress}%</span>
                            </div>
                            <div className="w-full bg-slate-700 rounded-full h-1.5">
                              <div
                            className={cn(
                              "h-1.5 rounded-full transition-all",
                              task.progress === 100 ? "bg-green-500" : "bg-blue-500"
                            )}
                            style={{ width: `${task.progress}%` }} />
                            </div>
                      </div>
                      }

                        {task.description &&
                      <div className="text-xs text-slate-300 line-clamp-2 mt-2">
                            {task.description}
                      </div>
                      }
                      </div>
                    </CardContent>
                </Card>);

            })}

              {getTasksByStatus(status).length === 0 &&
            <div className="text-center py-8 text-slate-500 text-sm">
                  暂无任务
            </div>
            }
            </div>
        </div>
        )}
      </div>

      {/* 创建任务对话框 */}
      <Dialog open={showTaskDialog} onOpenChange={setShowTaskDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>创建执行任务</DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">任务名称 *</label>
              <Input
                value={taskForm.task_name}
                onChange={(e) =>
                setTaskForm({ ...taskForm, task_name: e.target.value })
                }
                placeholder="请输入任务名称" />

            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">任务类型 *</label>
                <Select
                  value={taskForm.task_type}
                  onValueChange={(value) =>
                  setTaskForm({ ...taskForm, task_type: value })
                  }>

                  <SelectTrigger>
                    <SelectValue placeholder="选择任务类型" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(taskTypeConfigs).map(([key, config]) =>
                    <SelectItem key={key} value={key || "unknown"}>
                        {config.label}
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">责任部门 *</label>
                <Input
                  value={taskForm.task_dept}
                  onChange={(e) =>
                  setTaskForm({ ...taskForm, task_dept: e.target.value })
                  }
                  placeholder="如：机械部、电气部等" />

              </div>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">任务描述</label>
              <Textarea
                value={taskForm.task_description}
                onChange={(e) =>
                setTaskForm({ ...taskForm, task_description: e.target.value })
                }
                placeholder="详细描述任务内容和要求"
                rows={4} />

            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">计划开始日期</label>
                <Input
                  type="date"
                  value={taskForm.planned_start}
                  onChange={(e) =>
                  setTaskForm({ ...taskForm, planned_start: e.target.value })
                  } />

              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">计划结束日期</label>
                <Input
                  type="date"
                  value={taskForm.planned_end}
                  onChange={(e) =>
                  setTaskForm({ ...taskForm, planned_end: e.target.value })
                  } />

              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowTaskDialog(false)}>

              取消
            </Button>
            <Button onClick={handleCreateTask}>创建任务</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>);

}