/**
 * ProjectView - Tasks grouped by project with stats
 */

import { useNavigate } from "react-router-dom";
import {
  Briefcase,
  Box,
} from "lucide-react";
import {
  Card,
  CardContent,
  Button,
} from "../../components/ui";
import TaskListItem from "./TaskListItem";

export default function ProjectView({
  filteredTasks,
  handleTaskSelect,
  selectedTask,
  searchQuery,
  statusFilter,
  projectFilter,
}) {
  const navigate = useNavigate();

  // Group tasks by project
  const tasksByProject = {};
  (filteredTasks || []).forEach((task) => {
    const projectId = task.projectId || "other";
    const projectName = task.projectName || "未分配项目";
    if (!tasksByProject[projectId]) {
      tasksByProject[projectId] = {
        projectId,
        projectName,
        tasks: [],
        stats: {
          total: 0,
          inProgress: 0,
          completed: 0,
          pending: 0
        }
      };
    }
    tasksByProject[projectId].tasks.push(task);
    tasksByProject[projectId].stats.total++;
    if (task.status === "in_progress")
    {tasksByProject[projectId].stats.inProgress++;}else
    if (task.status === "completed")
    {tasksByProject[projectId].stats.completed++;}else
    if (task.status === "pending")
    {tasksByProject[projectId].stats.pending++;}
  });

  const projectGroups = Object.values(tasksByProject);

  if (projectGroups.length === 0) {
    return (
      <div className="text-center py-16">
          <Box className="w-16 h-16 mx-auto text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-slate-400">
            暂无任务
          </h3>
          <p className="text-sm text-slate-500 mt-1">
            {searchQuery ||
          statusFilter !== "all" ||
          projectFilter !== "all" ?
          "没有符合条件的任务" :
          "当前没有分配给您的设计任务"}
          </p>
      </div>);

  }

  return (
    <div className="space-y-6">
      {(projectGroups || []).map((group) =>
      <Card key={group.projectId} className="bg-surface-1/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Briefcase className="w-5 h-5 text-primary" />
                  <div>
                    <h3 className="text-lg font-semibold">
                      {group.projectName}
                    </h3>
                    <p className="text-sm text-slate-400">
                      {group.projectId}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-sm text-slate-400">总任务</p>
                    <p className="text-xl font-bold">
                      {group.stats.total}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-slate-400">进行中</p>
                    <p className="text-xl font-bold text-blue-400">
                      {group.stats.inProgress}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-slate-400">已完成</p>
                    <p className="text-xl font-bold text-emerald-400">
                      {group.stats.completed}
                    </p>
                  </div>
                  <Button
                variant="ghost"
                size="sm"
                onClick={() =>
                navigate(`/projects/${group.projectId}/workspace`)
                }>

                    查看工作空间
                  </Button>
                </div>
              </div>
              <div className="space-y-2">
                {(group.tasks || []).map((task) =>
            <TaskListItem
              key={task.id}
              task={task}
              onClick={handleTaskSelect}
              isSelected={selectedTask?.id === task.id} />

            )}
              </div>
            </CardContent>
      </Card>
      )}
    </div>
  );
}
