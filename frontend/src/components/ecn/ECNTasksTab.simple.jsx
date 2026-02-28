/**
 * ECN执行任务标签页组件（简化版）
 * 用途：展示和管理ECN的执行任务（看板视图）
 */
import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Plus } from 'lucide-react';
import { taskStatusConfigs } from '@/lib/constants/ecn';

/**
 * 任务卡片组件
 */
const TaskCard = ({ task, onUpdateProgress, onComplete, formatDate }) => {
  const isInProgress = task.status === 'IN_PROGRESS';

  return (
    <Card className="p-3 hover:shadow-md transition-shadow">
      <div className="space-y-2">
        {/* 任务名称 */}
        <div className="font-medium text-sm">{task.task_name}</div>

        {/* 部门 */}
        {task.task_dept && (
          <div className="text-xs text-slate-500">
            部门: {task.task_dept}
          </div>
        )}

        {/* 负责人 */}
        {task.assignee_name && (
          <div className="text-xs text-slate-500">
            负责人: {task.assignee_name}
          </div>
        )}

        {/* 计划时间 */}
        {task.planned_start && (
          <div className="text-xs text-slate-500">
            计划: {formatDate(task.planned_start)}
            {task.planned_end ? ` - ${formatDate(task.planned_end)}` : ''}
          </div>
        )}

        {/* 进度条（仅进行中状态） */}
        {isInProgress && (
          <div className="space-y-1 pt-2">
            <div className="flex justify-between text-xs">
              <span className="text-slate-500">进度</span>
              <span className="font-semibold">{task.progress_pct || 0}%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all"
                style={{ width: `${task.progress_pct || 0}%` }}
              />
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={task.progress_pct || 0}
              onChange={(e) =>
                onUpdateProgress(task.id, parseInt(e.target.value))
              }
              className="w-full"
            />
          </div>
        )}

        {/* 完成按钮（仅进行中状态） */}
        {isInProgress && (
          <Button
            size="sm"
            className="w-full mt-2"
            onClick={() => onComplete(task.id)}
          >
            完成任务
          </Button>
        )}
      </div>
    </Card>
  );
};

/**
 * 任务列组件
 */
const TaskColumn = ({ status, tasks, onUpdateProgress, onComplete, formatDate }) => {
  const statusConfig = taskStatusConfigs[status] || { label: status, color: 'bg-slate-500' };

  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold">
            {statusConfig.label}
          </CardTitle>
          <Badge className={statusConfig.color}>{tasks?.length}</Badge>
        </div>
      </CardHeader>
      <CardContent className="flex-1 space-y-3 overflow-y-auto max-h-[600px]">
        {tasks?.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-sm">
            暂无任务
          </div>
        ) : (
          (tasks || []).map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onUpdateProgress={onUpdateProgress}
              onComplete={onComplete}
              formatDate={formatDate}
            />
          ))
        )}
      </CardContent>
    </Card>
  );
};

/**
 * ECN执行任务标签页主组件
 */
export const ECNTasksTab = ({
  ecnStatus,
  tasks = [],
  onCreateTask,
  onUpdateProgress,
  onCompleteTask,
  formatDate,
}) => {
  // 是否允许创建任务
  const canCreateTask = ecnStatus === 'APPROVED' || ecnStatus === 'EXECUTING';

  // 按状态分组任务
  const tasksByStatus = {
    PENDING: (tasks || []).filter((t) => t.status === 'PENDING'),
    IN_PROGRESS: (tasks || []).filter((t) => t.status === 'IN_PROGRESS'),
    COMPLETED: (tasks || []).filter((t) => t.status === 'COMPLETED'),
  };

  return (
    <div className="space-y-4">
      {/* 创建任务按钮 */}
      <div className="flex justify-end gap-2">
        {canCreateTask && (
          <Button onClick={onCreateTask}>
            <Plus className="w-4 h-4 mr-2" />
            创建任务
          </Button>
        )}
      </div>

      {/* 任务看板 */}
      {tasks?.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-slate-400">
            暂无执行任务
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          {['PENDING', 'IN_PROGRESS', 'COMPLETED'].map((status) => (
            <TaskColumn
              key={status}
              status={status}
              tasks={tasksByStatus[status]}
              onUpdateProgress={onUpdateProgress}
              onComplete={onCompleteTask}
              formatDate={formatDate}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default ECNTasksTab;
