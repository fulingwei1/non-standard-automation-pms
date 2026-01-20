/**
 * Project Task List Page - 项目任务列表页面
 * Features: 任务管理、依赖关系、负责人分配
 */
import { useState, useEffect, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Plus,
  Search,
  Filter,
  Edit,
  CheckCircle2,
  Circle,
  Clock,
  Users,
  AlertTriangle,
  GitBranch,
  Calendar,
  TrendingUp } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../components/ui/dialog";
import { cn, formatDate } from "../lib/utils";
import { progressApi, projectApi } from "../services/api";
const statusConfigs = {
  PENDING: { label: "待开始", color: "bg-slate-500", icon: Circle },
  IN_PROGRESS: { label: "进行中", color: "bg-blue-500", icon: Clock },
  BLOCKED: { label: "阻塞", color: "bg-red-500", icon: AlertTriangle },
  COMPLETED: { label: "已完成", color: "bg-emerald-500", icon: CheckCircle2 }
};
export default function ProjectTaskList() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [summary, setSummary] = useState(null);
  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterStage, setFilterStage] = useState("");
  const [filterAssignee, _setFilterAssignee] = useState("");
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showTaskDetail, setShowTaskDetail] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  // Form state
  const [newTask, setNewTask] = useState({
    task_name: "",
    stage: "",
    planned_start_date: "",
    planned_end_date: "",
    weight: 0,
    description: ""
  });
  useEffect(() => {
    if (id) {
      fetchProject();
      fetchTasks();
      fetchSummary();
    }
  }, [id, filterStatus, filterStage, filterAssignee]);
  const fetchProject = async () => {
    try {
      const res = await projectApi.get(id);
      setProject(res.data || res);
    } catch (error) {
      console.error("Failed to fetch project:", error);
    }
  };
  const fetchTasks = async () => {
    try {
      setLoading(true);
      const params = { project_id: id };
      if (filterStatus) {params.status = filterStatus;}
      if (filterStage) {params.stage = filterStage;}
      if (filterAssignee) {params.assignee_id = filterAssignee;}
      if (searchKeyword) {params.search = searchKeyword;}
      const res = await progressApi.tasks.list(params);
      const taskList = res.data?.items || res.data || [];
      setTasks(taskList);
    } catch (error) {
      console.error("Failed to fetch tasks:", error);
    } finally {
      setLoading(false);
    }
  };
  const fetchSummary = async () => {
    try {
      const res = await progressApi.reports.getSummary(id);
      setSummary(res.data || res);
    } catch (error) {
      console.error("Failed to fetch summary:", error);
    }
  };
  const handleCreateTask = async () => {
    if (!newTask.task_name) {
      alert("请填写任务名称");
      return;
    }
    try {
      await progressApi.tasks.create(id, newTask);
      setShowCreateDialog(false);
      setNewTask({
        task_name: "",
        stage: "",
        planned_start_date: "",
        planned_end_date: "",
        weight: 0,
        description: ""
      });
      fetchTasks();
      fetchSummary();
    } catch (error) {
      console.error("Failed to create task:", error);
      alert("创建任务失败: " + (error.response?.data?.detail || error.message));
    }
  };
  const handleViewTask = async (taskId) => {
    try {
      const res = await progressApi.tasks.get(taskId);
      setSelectedTask(res.data || res);
      setShowTaskDetail(true);
    } catch (error) {
      console.error("Failed to fetch task detail:", error);
    }
  };
  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          task.task_name?.toLowerCase().includes(keyword) ||
          task.description?.toLowerCase().includes(keyword));

      }
      return true;
    });
  }, [tasks, searchKeyword]);
  const getStatusIcon = (status) => {
    const config = statusConfigs[status];
    const Icon = config?.icon || Circle;
    return <Icon className="w-4 h-4" />;
  };
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/projects/${id}`)}>

            <ArrowLeft className="w-4 h-4 mr-2" />
            返回项目
          </Button>
          <PageHeader
            title={`${project?.project_name || "项目"} - 任务列表`}
            description="项目任务管理，支持任务创建、进度更新、依赖关系" />

        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建任务
        </Button>
      </div>
      {/* Summary Cards */}
      {summary &&
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">总任务数</div>
                  <div className="text-2xl font-bold">
                    {summary.total_tasks || 0}
                  </div>
                </div>
                <Circle className="w-8 h-8 text-slate-400" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">已完成</div>
                  <div className="text-2xl font-bold text-emerald-600">
                    {summary.completed_tasks || 0}
                  </div>
                </div>
                <CheckCircle2 className="w-8 h-8 text-emerald-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">进行中</div>
                  <div className="text-2xl font-bold text-blue-600">
                    {summary.in_progress_tasks || 0}
                  </div>
                </div>
                <Clock className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">整体进度</div>
                  <div className="text-2xl font-bold">
                    {summary.overall_progress || 0}%
                  </div>
                </div>
                <TrendingUp className="w-8 h-8 text-violet-500" />
              </div>
            </CardContent>
          </Card>
      </div>
      }
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索任务名称..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10" />

            </div>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger>
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                {Object.entries(statusConfigs).map(([key, config]) =>
                <SelectItem key={key} value={key}>
                    {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
            <Select value={filterStage} onValueChange={setFilterStage}>
              <SelectTrigger>
                <SelectValue placeholder="选择阶段" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部阶段</SelectItem>
                <SelectItem value="S1">S1-立项</SelectItem>
                <SelectItem value="S2">S2-设计</SelectItem>
                <SelectItem value="S3">S3-采购</SelectItem>
                <SelectItem value="S4">S4-生产</SelectItem>
                <SelectItem value="S5">S5-调试</SelectItem>
                <SelectItem value="S6">S6-验收</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      {/* Task List */}
      <Card>
        <CardHeader>
          <CardTitle>任务列表</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ?
          <div className="text-center py-8 text-slate-400">加载中...</div> :
          filteredTasks.length === 0 ?
          <div className="text-center py-8 text-slate-400">暂无任务</div> :

          <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>任务名称</TableHead>
                  <TableHead>阶段</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>负责人</TableHead>
                  <TableHead>计划日期</TableHead>
                  <TableHead>进度</TableHead>
                  <TableHead>权重</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTasks.map((task) => {
                const progress = task.progress || 0;
                const isOverdue =
                task.planned_end_date &&
                new Date(task.planned_end_date) < new Date() &&
                task.status !== "COMPLETED";
                return (
                  <TableRow key={task.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(task.status)}
                          <div>
                            <div className="font-medium">{task.task_name}</div>
                            {task.description &&
                          <div className="text-xs text-slate-500 line-clamp-1">
                                {task.description}
                          </div>
                          }
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{task.stage || "-"}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                        className={
                        statusConfigs[task.status]?.color || "bg-slate-500"
                        }>

                          {statusConfigs[task.status]?.label || task.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {task.assignee_name ?
                      <div className="flex items-center gap-2">
                            <Users className="w-4 h-4 text-slate-400" />
                            <span className="text-sm">
                              {task.assignee_name}
                            </span>
                      </div> :

                      <span className="text-slate-400">未分配</span>
                      }
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {task.planned_start_date ?
                        formatDate(task.planned_start_date) :
                        "-"}
                          {task.planned_end_date &&
                        <>
                              <span className="mx-1">-</span>
                              <span className={cn(isOverdue && "text-red-500")}>
                                {formatDate(task.planned_end_date)}
                              </span>
                        </>
                        }
                        </div>
                        {isOverdue &&
                      <Badge className="bg-red-500 text-xs mt-1">
                            逾期
                      </Badge>
                      }
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span>{progress}%</span>
                          </div>
                          <Progress value={progress} className="h-1.5" />
                        </div>
                      </TableCell>
                      <TableCell>
                        {task.weight ?
                      <Badge variant="outline">{task.weight}%</Badge> :

                      "-"
                      }
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewTask(task.id)}>

                            <Edit className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                  </TableRow>);

              })}
              </TableBody>
          </Table>
          }
        </CardContent>
      </Card>
      {/* Create Task Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建任务</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  任务名称 *
                </label>
                <Input
                  value={newTask.task_name}
                  onChange={(e) =>
                  setNewTask({ ...newTask, task_name: e.target.value })
                  }
                  placeholder="请输入任务名称" />

              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">阶段</label>
                <Select
                  value={newTask.stage}
                  onValueChange={(val) =>
                  setNewTask({ ...newTask, stage: val })
                  }>

                  <SelectTrigger>
                    <SelectValue placeholder="选择阶段" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="S1">S1-立项</SelectItem>
                    <SelectItem value="S2">S2-设计</SelectItem>
                    <SelectItem value="S3">S3-采购</SelectItem>
                    <SelectItem value="S4">S4-生产</SelectItem>
                    <SelectItem value="S5">S5-调试</SelectItem>
                    <SelectItem value="S6">S6-验收</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    计划开始日期
                  </label>
                  <Input
                    type="date"
                    value={newTask.planned_start_date}
                    onChange={(e) =>
                    setNewTask({
                      ...newTask,
                      planned_start_date: e.target.value
                    })
                    } />

                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    计划结束日期
                  </label>
                  <Input
                    type="date"
                    value={newTask.planned_end_date}
                    onChange={(e) =>
                    setNewTask({
                      ...newTask,
                      planned_end_date: e.target.value
                    })
                    } />

                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  权重 (%)
                </label>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  value={newTask.weight}
                  onChange={(e) =>
                  setNewTask({
                    ...newTask,
                    weight: parseFloat(e.target.value) || 0
                  })
                  }
                  placeholder="0" />

              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">描述</label>
                <Input
                  value={newTask.description}
                  onChange={(e) =>
                  setNewTask({ ...newTask, description: e.target.value })
                  }
                  placeholder="任务描述" />

              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}>

              取消
            </Button>
            <Button onClick={handleCreateTask}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Task Detail Dialog */}
      <Dialog open={showTaskDetail} onOpenChange={setShowTaskDetail}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>任务详情</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedTask &&
            <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">任务名称</div>
                    <div className="font-medium">{selectedTask.task_name}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">状态</div>
                    <Badge
                    className={statusConfigs[selectedTask.status]?.color}>

                      {statusConfigs[selectedTask.status]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">阶段</div>
                    <div>{selectedTask.stage || "-"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">负责人</div>
                    <div>{selectedTask.assignee_name || "未分配"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">计划开始</div>
                    <div>
                      {selectedTask.planned_start_date ?
                    formatDate(selectedTask.planned_start_date) :
                    "-"}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">计划结束</div>
                    <div>
                      {selectedTask.planned_end_date ?
                    formatDate(selectedTask.planned_end_date) :
                    "-"}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">进度</div>
                    <div className="space-y-1">
                      <div className="text-lg font-bold">
                        {selectedTask.progress || 0}%
                      </div>
                      <Progress
                      value={selectedTask.progress || 0}
                      className="h-2" />

                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">权重</div>
                    <div>{selectedTask.weight || 0}%</div>
                  </div>
                </div>
                {selectedTask.description &&
              <div>
                    <div className="text-sm text-slate-500 mb-1">描述</div>
                    <div>{selectedTask.description}</div>
              </div>
              }
            </div>
            }
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTaskDetail(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}