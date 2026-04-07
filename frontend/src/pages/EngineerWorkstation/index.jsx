/**
 * Engineer Workstation - Timeline-focused work interface for mechanical engineers
 * Features: Gantt chart, Calendar view, Task list with design deliverables
 */

import { useState, useEffect, useMemo, useCallback } from "react";
import {
  Calendar,
  CheckCircle2,
  Circle,
  PlayCircle,
  AlertTriangle,
} from "lucide-react";


import { cn } from "../../lib/utils";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { taskCenterApi } from "../../services/api";

// Import engineer components

// Import local sub-components and constants
import { taskTypeConfigs, statusConfigs, priorityConfigs, VIEW_MODES } from "./constants";

// Main Component
export default function EngineerWorkstation() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState("gantt");
  const [statusFilter, setStatusFilter] = useState("all");
  const [projectFilter, setProjectFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTask, setSelectedTask] = useState(null);
  const [detailPanelOpen, setDetailPanelOpen] = useState(false);

  // Map backend status to frontend status
  const mapBackendStatus = (backendStatus) => {
    const statusMap = {
      PENDING: "pending",
      ACCEPTED: "pending",
      IN_PROGRESS: "in_progress",
      COMPLETED: "completed",
      DONE: "completed",
      BLOCKED: "blocked",
      CANCELLED: "cancelled"
    };
    return (
      statusMap[backendStatus] || backendStatus?.toLowerCase() || "pending");

  };

  // Map frontend status to backend status
  const mapFrontendStatus = (frontendStatus) => {
    const statusMap = {
      pending: "PENDING",
      in_progress: "IN_PROGRESS",
      completed: "COMPLETED",
      blocked: "BLOCKED"
    };
    return statusMap[frontendStatus] || frontendStatus?.toUpperCase();
  };

  // Load engineer tasks
  const loadTasks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page: 1,
        page_size: 100
      };

      if (statusFilter !== "all") {
        params.status = mapFrontendStatus(statusFilter);
      }

      if (projectFilter !== "all") {
        params.project_id = parseInt(projectFilter);
      }

      if (searchQuery) {
        params.keyword = searchQuery;
      }

      const response = await taskCenterApi.myTasks(params);
      const tasksData = response.data?.items || response.data?.items || response.data || [];

      // Transform backend tasks to frontend format
      const transformedTasks = (tasksData || []).map((task) => ({
        id: task.id?.toString(),
        title: task.title || "",
        titleCn: task.title || task.description || "",
        projectId: task.project_id?.toString() || "",
        projectName: task.project_name || "",
        machineNo: task.source_name || "",
        type: task.task_type?.toLowerCase() || "design",
        status: mapBackendStatus(task.status),
        priority: task.priority?.toLowerCase() || "medium",
        progress: task.progress || 0,
        plannedStart: task.plan_start_date || task.plan_start || "",
        plannedEnd: task.plan_end_date || task.deadline || "",
        actualStart: task.actual_start_date || null,
        actualEnd: task.actual_end_date || null,
        estimatedHours: task.estimated_hours || 0,
        actualHours: parseFloat(task.actual_hours || 0),
        assignee: task.assignee_name || "",
        reviewer: task.assigner_name || "",
        milestone: null,
        milestoneDate: null,
        dependencies: [],
        deliverables: [],
        bomItems: 0,
        reviewStatus: "pending",
        notes: task.description || ""
      }));

      setTasks(transformedTasks);
    } catch (err) {
      console.error("Failed to load engineer tasks:", err);
      setError(err.response?.data?.detail || err.message || "加载任务列表失败");
      setTasks([]);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, projectFilter, searchQuery]);

  // Load tasks when component mounts or filters change
  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  // Get unique projects for filter
  const projects = useMemo(() => {
    const projectSet = new Set((tasks || []).map((t) => t.projectId));
    return Array.from(projectSet).map((id) => {
      const task = (tasks || []).find((t) => t.projectId === id);
      return { id, name: task.projectName };
    });
  }, [tasks]);

  // Filter tasks
  const filteredTasks = useMemo(() => {
    return (tasks || []).filter((task) => {
      if (statusFilter !== "all" && task.status !== statusFilter) {return false;}
      if (projectFilter !== "all" && task.projectId !== projectFilter)
      {return false;}
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          (task.titleCn || "").toLowerCase().includes(query) ||
          (task.projectName || "").toLowerCase().includes(query));

      }
      return true;
    });
  }, [tasks, statusFilter, projectFilter, searchQuery]);

  // Calculate stats
  const stats = useMemo(() => {
    const today = new Date();
    const weekEnd = new Date(today);
    weekEnd.setDate(weekEnd.getDate() + 7);

    return {
      inProgress: (tasks || []).filter((t) => t.status === "in_progress").length,
      pending: (tasks || []).filter((t) => t.status === "pending").length,
      completed: (tasks || []).filter((t) => t.status === "completed").length,
      dueThisWeek: (tasks || []).filter((t) => {
        const dueDate = new Date(t.plannedEnd);
        return (
          t.status !== "completed" && dueDate >= today && dueDate <= weekEnd);

      }).length,
      overdue: (tasks || []).filter((t) => {
        return t.status !== "completed" && new Date(t.plannedEnd) < today;
      }).length
    };
  }, [tasks]);

  // Handle task selection
  const handleTaskSelect = (task) => {
    setSelectedTask(task);
    setDetailPanelOpen(true);
  };

  // Handle task update
  const handleTaskUpdate = (taskId, updates) => {
    setTasks((prev) =>
    (prev || []).map((t) => t.id === taskId ? { ...t, ...updates } : t)
    );
    if (selectedTask?.id === taskId) {
      setSelectedTask((prev) => ({ ...prev, ...updates }));
    }
  };

  // Close detail panel
  const handleCloseDetail = () => {
    setDetailPanelOpen(false);
    setTimeout(() => setSelectedTask(null), 300);
  };

  // Show error state
  if (error && tasks?.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="我的工作台"
          description="机械设计任务管理 · 时间轴视图" />

        <ApiIntegrationError
          error={error}
          apiEndpoint="/api/v1/task-center/my-tasks"
          onRetry={loadTasks} />

      </div>);

  }

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="我的工作台"
          description="机械设计任务管理 · 时间轴视图" />

        <div className="text-center py-16">
          <div className="text-slate-400">加载中...</div>
        </div>
      </div>);

  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* Page Header */}
      <PageHeader
        title="我的工作台"
        description="机械设计任务管理 · 时间轴视图"
        actions={
        <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Upload className="w-4 h-4 mr-1" />
              上传文件
            </Button>
            <Button size="sm">
              <Send className="w-4 h-4 mr-1" />
              申请评审
            </Button>
        </div>
        } />


      {/* Stats Cards */}
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-2 md:grid-cols-5 gap-4">

        <StatsCard
          label="进行中"
          value={stats.inProgress}
          icon={PlayCircle}
          color="text-blue-400"
          onClick={() =>
          setStatusFilter(
            statusFilter === "in_progress" ? "all" : "in_progress"
          )
          }
          active={statusFilter === "in_progress"} />

        <StatsCard
          label="待开始"
          value={stats.pending}
          icon={Circle}
          color="text-slate-400"
          onClick={() =>
          setStatusFilter(statusFilter === "pending" ? "all" : "pending")
          }
          active={statusFilter === "pending"} />

        <StatsCard
          label="已完成"
          value={stats.completed}
          icon={CheckCircle2}
          color="text-emerald-400"
          onClick={() =>
          setStatusFilter(statusFilter === "completed" ? "all" : "completed")
          }
          active={statusFilter === "completed"} />

        <StatsCard
          label="本周到期"
          value={stats.dueThisWeek}
          icon={Calendar}
          color="text-amber-400" />

        <StatsCard
          label="已逾期"
          value={stats.overdue}
          icon={AlertTriangle}
          color="text-red-400" />

      </motion.div>

      {/* View Toggle & Filters */}
      <motion.div variants={fadeIn}>
        <Card className="bg-surface-1/50">
          <CardContent className="p-4">
            <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
              {/* View Mode Toggle */}
              <div className="flex items-center gap-1 p-1 bg-surface-2 rounded-lg">
                {Object.values(VIEW_MODES).map((mode) =>
                <Button
                  key={mode.id}
                  variant={viewMode === mode.id ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setViewMode(mode.id)}
                  className="gap-2">

                    <mode.icon className="w-4 h-4"  />
                    {mode.label}
                </Button>
                )}
              </div>

              {/* Filters */}
              <div className="flex items-center gap-3 flex-wrap">
                {/* Project Filter */}
                <select
                  value={projectFilter || "unknown"}
                  onChange={(e) => setProjectFilter(e.target.value)}
                  className="h-9 px-3 rounded-lg bg-surface-2 border border-border text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/50">

                  <option value="all">全部项目</option>
                  {(projects || []).map((p) =>
                  <option key={p.id} value={p.id}>
                      {p.name}
                  </option>
                  )}
                </select>

                {/* Status Filter */}
                <select
                  value={statusFilter || "unknown"}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="h-9 px-3 rounded-lg bg-surface-2 border border-border text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/50">

                  <option value="all">全部状态</option>
                  <option value="in_progress">进行中</option>
                  <option value="pending">待开始</option>
                  <option value="blocked">已阻塞</option>
                  <option value="completed">已完成</option>
                </select>

                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    placeholder="搜索任务..."
                    value={searchQuery || "unknown"}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9 w-48" />

                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Main Content Area */}
      <motion.div variants={fadeIn} className="relative">
        <div
          className={cn(
            "transition-all duration-300",
            detailPanelOpen ? "mr-96" : ""
          )}>

          {/* Gantt View */}
          {viewMode === "gantt" &&
          <GanttChart
            tasks={filteredTasks}
            onTaskSelect={handleTaskSelect}
            selectedTaskId={selectedTask?.id} />

          }

          {/* Calendar View */}
          {viewMode === "calendar" &&
          <CalendarView
            tasks={filteredTasks}
            onTaskSelect={handleTaskSelect}
            selectedTaskId={selectedTask?.id} />

          }

          {/* List View */}
          {viewMode === "list" &&
          <div className="space-y-3">
              {(filteredTasks || []).map((task) =>
            <TaskListItem
              key={task.id}
              task={task}
              onClick={handleTaskSelect}
              isSelected={selectedTask?.id === task.id} />

            )}

              {filteredTasks.length === 0 &&
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
            </div>
            }
          </div>
          }

          {/* Project View */}
          {viewMode === "project" &&
          <ProjectView
            filteredTasks={filteredTasks}
            handleTaskSelect={handleTaskSelect}
            selectedTask={selectedTask}
            searchQuery={searchQuery}
            statusFilter={statusFilter}
            projectFilter={projectFilter} />

          }
        </div>

        {/* Task Detail Panel */}
        <AnimatePresence>
          {detailPanelOpen && selectedTask &&
          <TaskDetailPanel
            task={selectedTask}
            onClose={handleCloseDetail}
            onUpdate={handleTaskUpdate}
            statusConfigs={statusConfigs}
            priorityConfigs={priorityConfigs}
            taskTypeConfigs={taskTypeConfigs} />

          }
        </AnimatePresence>
      </motion.div>
    </motion.div>);

}
