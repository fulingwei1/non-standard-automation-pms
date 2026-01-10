/**
 * ECNTasksTab Component
 * ECN 执行任务 Tab 组件（看板视图）
 */
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Plus } from "lucide-react";
import { formatDate } from "../../lib/utils";
import { useECNTasks } from "./hooks/useECNTasks";
import TaskDialog from "./dialogs/TaskDialog";

const taskStatusConfigs = {
  PENDING: { label: "待开始", color: "bg-slate-500" },
  IN_PROGRESS: { label: "进行中", color: "bg-blue-500" },
  COMPLETED: { label: "已完成", color: "bg-green-500" },
};

export default function ECNTasksTab({ ecnId, ecn, tasks, refetch }) {
  const {
    showTaskDialog,
    setShowTaskDialog,
    taskForm,
    setTaskForm,
    handleCreateTask,
    handleUpdateTaskProgress,
    handleCompleteTask,
  } = useECNTasks(ecnId, refetch);

  // 处理创建任务
  const handleCreateClick = async () => {
    const result = await handleCreateTask();
    if (result.success) {
      alert(result.message);
    } else {
      alert(result.message);
    }
  };

  // 处理更新进度
  const handleProgressChange = async (taskId, progress) => {
    await handleUpdateTaskProgress(taskId, progress);
    // 不显示提示，静默更新
  };

  // 处理完成任务
  const handleCompleteClick = async (taskId) => {
    const result = await handleCompleteTask(taskId);
    if (result.success) {
      alert(result.message);
    } else {
      alert(result.message);
    }
  };

  // 判断是否可以创建任务
  const canCreateTask =
    ecn?.status === "APPROVED" || ecn?.status === "EXECUTING";

  // 按状态分组任务
  const tasksByStatus = {
    PENDING: tasks.filter((t) => t.status === "PENDING"),
    IN_PROGRESS: tasks.filter((t) => t.status === "IN_PROGRESS"),
    COMPLETED: tasks.filter((t) => t.status === "COMPLETED"),
  };

  return (
    <div className="space-y-4">
      {/* 创建任务按钮 */}
      <div className="flex justify-end gap-2">
        {canCreateTask && (
          <Button onClick={() => setShowTaskDialog(true)}>
            <Plus className="w-4 h-4 mr-2" />
            创建任务
          </Button>
        )}
      </div>

      {/* 任务看板 */}
      {tasks.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-slate-400">
            暂无执行任务
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          {["PENDING", "IN_PROGRESS", "COMPLETED"].map((status) => {
            const statusTasks = tasksByStatus[status];
            const statusConfig = taskStatusConfigs[status];

            return (
              <Card key={status} className="flex flex-col">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold">
                      {statusConfig?.label || status}
                    </CardTitle>
                    <Badge className={statusConfig?.color}>
                      {statusTasks.length}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="flex-1 space-y-3 overflow-y-auto max-h-[600px]">
                  {statusTasks.length === 0 ? (
                    <div className="text-center py-8 text-slate-400 text-sm">
                      暂无任务
                    </div>
                  ) : (
                    statusTasks.map((task) => (
                      <Card
                        key={task.id}
                        className="p-3 hover:shadow-md transition-shadow"
                      >
                        <div className="space-y-2">
                          <div className="font-medium text-sm">
                            {task.task_name}
                          </div>
                          {task.task_dept && (
                            <div className="text-xs text-slate-500">
                              部门: {task.task_dept}
                            </div>
                          )}
                          {task.assignee_name && (
                            <div className="text-xs text-slate-500">
                              负责人: {task.assignee_name}
                            </div>
                          )}
                          {task.planned_start && (
                            <div className="text-xs text-slate-500">
                              计划: {formatDate(task.planned_start)}
                              {task.planned_end
                                ? ` - ${formatDate(task.planned_end)}`
                                : ""}
                            </div>
                          )}
                          {task.status === "IN_PROGRESS" && (
                            <div className="space-y-1 pt-2">
                              <div className="flex justify-between text-xs">
                                <span className="text-slate-500">进度</span>
                                <span className="font-semibold">
                                  {task.progress_pct || 0}%
                                </span>
                              </div>
                              <div className="w-full bg-slate-200 rounded-full h-2">
                                <div
                                  className="bg-blue-500 h-2 rounded-full transition-all"
                                  style={{
                                    width: `${task.progress_pct || 0}%`,
                                  }}
                                />
                              </div>
                              <input
                                type="range"
                                min="0"
                                max="100"
                                value={task.progress_pct || 0}
                                onChange={(e) =>
                                  handleProgressChange(
                                    task.id,
                                    parseInt(e.target.value),
                                  )
                                }
                                className="w-full"
                              />
                            </div>
                          )}
                          {task.status === "IN_PROGRESS" && (
                            <Button
                              size="sm"
                              className="w-full mt-2"
                              onClick={() => handleCompleteClick(task.id)}
                            >
                              完成任务
                            </Button>
                          )}
                        </div>
                      </Card>
                    ))
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* 创建任务对话框 */}
      <TaskDialog
        open={showTaskDialog}
        onOpenChange={setShowTaskDialog}
        form={taskForm}
        setForm={setTaskForm}
        onSubmit={handleCreateClick}
      />
    </div>
  );
}
