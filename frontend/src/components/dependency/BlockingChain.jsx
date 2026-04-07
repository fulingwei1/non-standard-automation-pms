/**
 * BlockingChain - 阻塞链可视化组件
 * 给定任务ID，展示上下游阻塞链，支持点击展开详情
 */

import { useState, useEffect, useMemo, useCallback } from "react";
import {
  AlertTriangle,
  CheckCircle,
  Clock,
} from "lucide-react";


import { ganttDependencyApi } from "../../services/api";
import { formatDate, cn } from "../../lib/utils";

// 任务状态配置
const TASK_STATUS_CONFIG = {
  DONE: {
    label: "已完成",
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/20",
    borderColor: "border-emerald-500/50",
    icon: CheckCircle,
  },
  COMPLETED: {
    label: "已完成",
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/20",
    borderColor: "border-emerald-500/50",
    icon: CheckCircle,
  },
  IN_PROGRESS: {
    label: "进行中",
    color: "text-blue-400",
    bgColor: "bg-blue-500/20",
    borderColor: "border-blue-500/50",
    icon: Clock,
  },
  PENDING: {
    label: "待开始",
    color: "text-slate-400",
    bgColor: "bg-slate-500/20",
    borderColor: "border-slate-500/50",
    icon: Clock,
  },
  TODO: {
    label: "待开始",
    color: "text-slate-400",
    bgColor: "bg-slate-500/20",
    borderColor: "border-slate-500/50",
    icon: Clock,
  },
  BLOCKED: {
    label: "阻塞",
    color: "text-red-400",
    bgColor: "bg-red-500/20",
    borderColor: "border-red-500/50",
    icon: AlertTriangle,
  },
};

// 获取任务状态配置
const getStatusConfig = (status) => {
  return TASK_STATUS_CONFIG[status] || TASK_STATUS_CONFIG.PENDING;
};

// 阻塞链节点组件
function BlockingNode({ task, isCenter, isBlocking, isBlocked, onClick, isHighlighted }) {
  const statusConfig = getStatusConfig(task.status);
  const StatusIcon = statusConfig.icon;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn(
        "relative p-4 rounded-lg border-2 cursor-pointer transition-all",
        statusConfig.bgColor,
        isHighlighted ? "ring-2 ring-cyan-400" : "",
        isCenter ? "border-cyan-500 ring-2 ring-cyan-400/50" : statusConfig.borderColor,
        "hover:shadow-lg hover:scale-105"
      )}
      onClick={() => onClick && onClick(task)}
    >
      {/* 阻塞标识 */}
      {isBlocking && (
        <div className="absolute -top-2 -left-2">
          <Badge className="bg-red-500 text-white text-xs">阻塞源</Badge>
        </div>
      )}
      {isBlocked && (
        <div className="absolute -top-2 -right-2">
          <Badge className="bg-amber-500 text-white text-xs">被阻塞</Badge>
        </div>
      )}

      <div className="flex items-start gap-3">
        <StatusIcon className={cn("h-5 w-5 mt-0.5", statusConfig.color)} />
        <div className="flex-1 min-w-0">
          <div className="font-medium text-sm truncate">{task.task_name}</div>
          <div className="flex items-center gap-2 mt-1 text-xs text-slate-400">
            <Badge variant="outline" className="text-[10px]">
              {statusConfig.label}
            </Badge>
            {task.assignee_name && (
              <span className="flex items-center gap-1">
                <User className="h-3 w-3" />
                {task.assignee_name}
              </span>
            )}
          </div>
          {task.plan_end && (
            <div className="flex items-center gap-1 mt-1 text-xs text-slate-500">
              <Calendar className="h-3 w-3" />
              {formatDate(task.plan_end)}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

// 依赖箭头组件
function DependencyArrow({ isCritical }) {
  return (
    <div className="flex items-center justify-center px-2">
      <div
        className={cn(
          "flex items-center gap-1",
          isCritical ? "text-red-400" : "text-slate-500"
        )}
      >
        <div className={cn("w-8 h-px", isCritical ? "bg-red-400" : "bg-slate-500")} />
        <ArrowRight className="h-4 w-4" />
      </div>
    </div>
  );
}

// 任务详情弹窗
function TaskDetailDialog({ task, open, onClose }) {
  if (!task) return null;

  const statusConfig = getStatusConfig(task.status);

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>任务详情</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <div className="text-sm text-slate-400">任务名称</div>
            <div className="font-medium">{task.task_name}</div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-slate-400">状态</div>
              <Badge className={cn("mt-1", statusConfig.bgColor, statusConfig.color)}>
                {statusConfig.label}
              </Badge>
            </div>
            <div>
              <div className="text-sm text-slate-400">进度</div>
              <div className="font-medium">{task.progress_percent || 0}%</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-slate-400">负责人</div>
              <div className="font-medium">{task.assignee_name || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400">阶段</div>
              <div className="font-medium">{task.stage || "-"}</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-slate-400">计划开始</div>
              <div className="font-medium">{formatDate(task.plan_start) || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400">计划结束</div>
              <div className="font-medium">{formatDate(task.plan_end) || "-"}</div>
            </div>
          </div>

          {task.delay_reason && (
            <div>
              <div className="text-sm text-slate-400">延期原因</div>
              <div className="p-2 bg-red-500/10 rounded text-sm text-red-300">
                {task.delay_reason}
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// 主组件
export default function BlockingChain({
  projectId,
  taskId,
  onClose,
  showAsModal = false,
}) {
  const [loading, setLoading] = useState(true);
  const [tasks, setTasks] = useState([]);
  const [dependencies, setDependencies] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [showTaskDetail, setShowTaskDetail] = useState(false);

  // 获取依赖数据
  const fetchData = useCallback(async () => {
    if (!projectId) return;

    setLoading(true);
    try {
      const res = await ganttDependencyApi.getGantt(projectId);
      const data = res.data || res || {};

      setTasks(data.tasks || []);
      setDependencies(data.dependencies || []);
    } catch (error) {
      console.error("Failed to fetch dependency data:", error);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // 构建阻塞链
  const blockingChain = useMemo(() => {
    if (!taskId || tasks.length === 0) return { upstream: [], center: null, downstream: [] };

    const centerTask = tasks.find((t) => t.id === taskId);
    if (!centerTask) return { upstream: [], center: null, downstream: [] };

    // 找上游任务（阻塞当前任务的）
    const upstreamIds = new Set();
    const findUpstream = (id, visited = new Set()) => {
      if (visited.has(id)) return;
      visited.add(id);

      dependencies.forEach((dep) => {
        if (dep.task_id === id && !visited.has(dep.depends_on_task_id)) {
          upstreamIds.add(dep.depends_on_task_id);
          findUpstream(dep.depends_on_task_id, visited);
        }
      });
    };
    findUpstream(taskId);

    // 找下游任务（被当前任务阻塞的）
    const downstreamIds = new Set();
    const findDownstream = (id, visited = new Set()) => {
      if (visited.has(id)) return;
      visited.add(id);

      dependencies.forEach((dep) => {
        if (dep.depends_on_task_id === id && !visited.has(dep.task_id)) {
          downstreamIds.add(dep.task_id);
          findDownstream(dep.task_id, visited);
        }
      });
    };
    findDownstream(taskId);

    // 只取直接上下游（限制深度为 2 层）
    const directUpstream = dependencies
      .filter((dep) => dep.task_id === taskId)
      .map((dep) => dep.depends_on_task_id);

    const directDownstream = dependencies
      .filter((dep) => dep.depends_on_task_id === taskId)
      .map((dep) => dep.task_id);

    return {
      upstream: tasks
        .filter((t) => directUpstream.includes(t.id))
        .slice(0, 3),
      center: centerTask,
      downstream: tasks
        .filter((t) => directDownstream.includes(t.id))
        .slice(0, 3),
      totalUpstream: upstreamIds.size,
      totalDownstream: downstreamIds.size,
    };
  }, [taskId, tasks, dependencies]);

  // 处理任务点击
  const handleTaskClick = (task) => {
    setSelectedTask(task);
    setShowTaskDetail(true);
  };

  // 渲染内容
  const renderContent = () => {
    if (loading) {
      return (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <div className="flex items-center gap-4">
            <Skeleton className="h-20 w-1/3" />
            <Skeleton className="h-20 w-1/3" />
            <Skeleton className="h-20 w-1/3" />
          </div>
        </div>
      );
    }

    if (!blockingChain.center) {
      return (
        <div className="text-center py-8 text-slate-400">
          未找到指定任务的依赖关系
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {/* 阻塞链可视化 */}
        <div className="flex items-center justify-center gap-2 overflow-x-auto py-4">
          {/* 上游任务 */}
          {blockingChain.upstream.length > 0 && (
            <>
              <div className="flex flex-col gap-2 min-w-[200px]">
                {blockingChain.upstream.map((task) => (
                  <BlockingNode
                    key={task.id}
                    task={task}
                    isBlocking={task.status !== "DONE" && task.status !== "COMPLETED"}
                    onClick={handleTaskClick}
                  />
                ))}
                {blockingChain.totalUpstream > blockingChain.upstream.length && (
                  <div className="text-center text-xs text-slate-500">
                    +{blockingChain.totalUpstream - blockingChain.upstream.length} 更多上游任务
                  </div>
                )}
              </div>
              <DependencyArrow
                isCritical={blockingChain.upstream.some(
                  (t) => t.status !== "DONE" && t.status !== "COMPLETED"
                )}
              />
            </>
          )}

          {/* 中心任务 */}
          <div className="min-w-[220px]">
            <BlockingNode
              task={blockingChain.center}
              isCenter
              onClick={handleTaskClick}
              isHighlighted
            />
          </div>

          {/* 下游任务 */}
          {blockingChain.downstream.length > 0 && (
            <>
              <DependencyArrow
                isCritical={
                  blockingChain.center.status !== "DONE" &&
                  blockingChain.center.status !== "COMPLETED"
                }
              />
              <div className="flex flex-col gap-2 min-w-[200px]">
                {blockingChain.downstream.map((task) => (
                  <BlockingNode
                    key={task.id}
                    task={task}
                    isBlocked={
                      blockingChain.center.status !== "DONE" &&
                      blockingChain.center.status !== "COMPLETED"
                    }
                    onClick={handleTaskClick}
                  />
                ))}
                {blockingChain.totalDownstream > blockingChain.downstream.length && (
                  <div className="text-center text-xs text-slate-500">
                    +{blockingChain.totalDownstream - blockingChain.downstream.length} 更多下游任务
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* 阻塞分析 */}
        {(blockingChain.upstream.length > 0 || blockingChain.downstream.length > 0) && (
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">阻塞分析</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {blockingChain.upstream.some(
                (t) => t.status !== "DONE" && t.status !== "COMPLETED"
              ) && (
                <div className="flex items-start gap-2 p-2 bg-red-500/10 rounded">
                  <AlertTriangle className="h-4 w-4 text-red-400 mt-0.5" />
                  <div>
                    <div className="font-medium text-red-300">存在阻塞</div>
                    <div className="text-slate-400">
                      有 {blockingChain.upstream.filter(
                        (t) => t.status !== "DONE" && t.status !== "COMPLETED"
                      ).length} 个前置任务未完成，阻塞当前任务的执行
                    </div>
                  </div>
                </div>
              )}

              {blockingChain.center.status !== "DONE" &&
                blockingChain.center.status !== "COMPLETED" &&
                blockingChain.downstream.length > 0 && (
                <div className="flex items-start gap-2 p-2 bg-amber-500/10 rounded">
                  <Clock className="h-4 w-4 text-amber-400 mt-0.5" />
                  <div>
                    <div className="font-medium text-amber-300">影响下游</div>
                    <div className="text-slate-400">
                      当前任务影响 {blockingChain.totalDownstream} 个下游任务的启动
                    </div>
                  </div>
                </div>
              )}

              {blockingChain.upstream.every(
                (t) => t.status === "DONE" || t.status === "COMPLETED"
              ) &&
                blockingChain.upstream.length > 0 && (
                <div className="flex items-start gap-2 p-2 bg-emerald-500/10 rounded">
                  <CheckCircle className="h-4 w-4 text-emerald-400 mt-0.5" />
                  <div>
                    <div className="font-medium text-emerald-300">无阻塞</div>
                    <div className="text-slate-400">
                      所有前置任务已完成，当前任务可以执行
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  // 如果是弹窗模式
  if (showAsModal) {
    return (
      <>
        <Dialog open onOpenChange={onClose}>
          <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-400" />
                阻塞链分析
              </DialogTitle>
            </DialogHeader>
            {renderContent()}
          </DialogContent>
        </Dialog>

        <TaskDetailDialog
          task={selectedTask}
          open={showTaskDetail}
          onClose={() => setShowTaskDetail(false)}
        />
      </>
    );
  }

  // 卡片模式
  return (
    <>
      <Card className="bg-slate-900/50 border-slate-800">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400" />
            阻塞链分析
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={fetchData}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent>{renderContent()}</CardContent>
      </Card>

      <TaskDetailDialog
        task={selectedTask}
        open={showTaskDetail}
        onClose={() => setShowTaskDetail(false)}
      />
    </>
  );
}
