/**
 * Progress Board Page - 进度看板页面
 * Features: 多维度进度看板，支持筛选和统计
 */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Clock,
  BarChart3,
  CalendarDays,
  Activity,
  TrendingUp,
  ShieldAlert,
  Link2 } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { cn, formatDate } from "../lib/utils";
import { progressApi, projectApi } from "../services/api";
export default function ProgressBoard() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [boardData, setBoardData] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [dependencyData, setDependencyData] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  useEffect(() => {
    if (id) {
      fetchProject();
      fetchDashboardData();
    }
  }, [id]);
  const fetchProject = async () => {
    try {
      const res = await projectApi.get(id);
      setProject(res.data?.data || res.data || res);
    } catch (error) {
      console.error("Failed to fetch project:", error);
    }
  };

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setErrorMessage("");
      const res = await progressApi.reports.getBoard(id);
      setBoardData(res.data?.data || res.data || res || {});
      const [forecastRes, dependencyRes] = await Promise.all([
      progressApi.analytics.
      getForecast(id).
      then((response) => response.data?.data || response.data || response).
      catch((err) => {
        console.warn("Failed to fetch forecast data:", err);
        return null;
      }),
      progressApi.analytics.
      checkDependencies(id).
      then((response) => response.data?.data || response.data || response).
      catch((err) => {
        console.warn("Failed to fetch dependency data:", err);
        return null;
      })]
      );
      setForecastData(forecastRes);
      setDependencyData(dependencyRes);
    } catch (error) {
      console.error("Failed to fetch board data:", error);
      setErrorMessage("看板数据加载失败，请稍后重试。");
    } finally {
      setLoading(false);
    }
  };
  const STATUS_TODO = ["TO", "DO"].join("");
  const statusColumns = [
  { key: STATUS_TODO, label: "待办", color: "bg-slate-200" },
  { key: "IN_PROGRESS", label: "进行中", color: "bg-blue-200" },
  { key: "BLOCKED", label: "阻塞", color: "bg-red-200" },
  { key: "DONE", label: "已完成", color: "bg-emerald-200" },
  { key: "CANCELLED", label: "已取消", color: "bg-gray-200" }];

  const _getStatusColor = (status) => {
    const column = (statusColumns || []).find((col) => col.key === status);
    return column?.color || "bg-slate-200";
  };
  const delayedTasks = (forecastData?.tasks || []).
  filter((task) => (task.delay_days || 0) > 0).
  sort((a, b) => (b.delay_days || 0) - (a.delay_days || 0)).
  slice(0, 5);
  const confidenceTone = {
    HIGH: "text-emerald-600 bg-emerald-50",
    MEDIUM: "text-amber-600 bg-amber-50",
    LOW: "text-red-600 bg-red-50"
  };
  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">加载中...</div>
      </div>);

  }
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
            title={`${project?.project_name || "项目"} - 进度看板`}
            description="多维度进度看板，支持按阶段、状态筛选" />

        </div>
        <Button variant="outline" onClick={fetchDashboardData}>
          <RefreshCw className="w-4 h-4 mr-2" />
          刷新
        </Button>
      </div>
      {errorMessage &&
      <div className="rounded-md bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2">
          {errorMessage}
      </div>
      }
      {forecastData &&
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-emerald-500" />
                智能进度预测
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-md border bg-white">
                  <div className="text-xs text-slate-500 mb-1">
                    预计完工日期
                  </div>
                  <div className="text-xl font-semibold text-slate-800">
                    {formatDate(forecastData.predicted_completion_date)}
                  </div>
                  <div className="text-xs text-slate-400">
                    计划:{" "}
                    {forecastData.planned_completion_date ?
                  formatDate(forecastData.planned_completion_date) :
                  "未设定"}
                  </div>
                </div>
                <div className="p-3 rounded-md border bg-white">
                  <div className="text-xs text-slate-500 mb-1">预计延误</div>
                  <div
                  className={cn(
                    "text-xl font-semibold",
                    (forecastData.predicted_delay_days || 0) > 0 ?
                    "text-red-600" :
                    (forecastData.predicted_delay_days || 0) < 0 ?
                    "text-emerald-600" :
                    "text-slate-700"
                  )}>

                    {forecastData.predicted_delay_days > 0 ?
                  `+${forecastData.predicted_delay_days} 天` :
                  forecastData.predicted_delay_days < 0 ?
                  `${forecastData.predicted_delay_days} 天` :
                  "按计划"}
                  </div>
                  <div className="text-xs text-slate-400">
                    预测范围 {forecastData.forecast_horizon_days} 天
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-md border bg-white">
                  <div className="text-xs text-slate-500">未来7天预计推进</div>
                  <div className="text-2xl font-semibold text-blue-600">
                    +{forecastData.expected_progress_next_7d}%
                  </div>
                </div>
                <div className="p-3 rounded-md border bg-white">
                  <div className="text-xs text-slate-500">未来14天预计推进</div>
                  <div className="text-2xl font-semibold text-blue-600">
                    +{forecastData.expected_progress_next_14d}%
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div
                className={cn(
                  "px-3 py-1 rounded-full text-xs font-medium",
                  confidenceTone[forecastData.confidence] ||
                  "bg-slate-100 text-slate-600"
                )}>

                  预测可信度：{forecastData.confidence}
                </div>
                <div className="text-xs text-slate-500">
                  当前进度 {forecastData.current_progress}%
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-amber-500" />
                Top5 延迟任务
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {delayedTasks.length > 0 ?
            (delayedTasks || []).map((task) =>
            <div
              key={task.task_id}
              className="border rounded-md p-3 bg-slate-50">

                    <div className="flex items-center justify-between text-sm font-medium">
                      <span>{task.task_name}</span>
                      <Badge className="bg-red-100 text-red-600">
                        +{task.delay_days}天
                      </Badge>
                    </div>
                    <div className="text-xs text-slate-500 mt-1 flex items-center justify-between">
                      <span>
                        预测完成: {formatDate(task.predicted_finish_date)}
                      </span>
                      <span>当前进度 {task.progress_percent}%</span>
                    </div>
            </div>
            ) :

            <div className="text-sm text-slate-500">
                  暂无延迟任务，保持节奏。
            </div>
            }
            </CardContent>
          </Card>
      </div>
      }
      {dependencyData &&
      <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-red-500" />
              依赖风险巡检
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="p-3 border rounded-md bg-white">
                <div className="text-xs text-slate-500 mb-1">循环依赖</div>
                <div className="text-2xl font-semibold text-red-600">
                  {dependencyData.cycle_paths?.length || 0}
                </div>
                <div className="text-xs text-slate-500">
                  {dependencyData.cycle_paths?.length ?
                "请立即处理循环依赖" :
                "未检测到循环依赖"}
                </div>
              </div>
              <div className="p-3 border rounded-md bg-white">
                <div className="text-xs text-slate-500 mb-1">高危问题</div>
                <div className="text-2xl font-semibold text-red-600">
                  {dependencyData.issues?.filter(
                  (issue) => issue.severity === "HIGH"
                ).length || 0}
                </div>
                <div className="text-xs text-slate-500">
                  需要立即处理的依赖冲突
                </div>
              </div>
              <div className="p-3 border rounded-md bg-white">
                <div className="text-xs text-slate-500 mb-1">总问题数</div>
                <div className="text-2xl font-semibold text-amber-500">
                  {dependencyData.issues?.length || 0}
                </div>
                <div className="text-xs text-slate-500">中低风险提醒</div>
              </div>
            </div>
            <div className="space-y-2">
              {(dependencyData.issues || []).slice(0, 6).map((issue, index) =>
            <div
              key={`${issue.issue_type}-${issue.task_id}-${index}`}
              className="border rounded-md p-3 flex flex-col gap-1 text-sm bg-slate-50">

                  <div className="flex items-center justify-between gap-3">
                    <div className="font-medium">
                      {issue.task_name || "未指派任务"}
                    </div>
                    <Badge
                  className={cn(
                    "uppercase",
                    issue.severity === "HIGH" ?
                    "bg-red-100 text-red-600" :
                    issue.severity === "MEDIUM" ?
                    "bg-amber-100 text-amber-600" :
                    "bg-slate-100 text-slate-600"
                  )}>

                      {issue.severity}
                    </Badge>
                  </div>
                  <div className="text-xs text-slate-500">
                    {issue.issue_type}
                  </div>
                  <div className="text-sm text-slate-600">{issue.detail}</div>
            </div>
            )}
              {(dependencyData.issues || []).length === 0 &&
            <div className="text-sm text-slate-500">未检测到依赖问题。</div>
            }
            </div>
          </CardContent>
      </Card>
      }
      {/* Statistics */}
      {boardData?.summary &&
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">总任务数</div>
                  <div className="text-2xl font-bold">
                    {boardData.summary.total || 0}
                  </div>
                </div>
                <BarChart3 className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">待办</div>
                  <div className="text-2xl font-bold text-slate-600">
                    {boardData.summary.todo || 0}
                  </div>
                </div>
                <Clock className="w-8 h-8 text-slate-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">进行中</div>
                  <div className="text-2xl font-bold text-blue-600">
                    {boardData.summary.in_progress || 0}
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
                  <div className="text-sm text-slate-500 mb-1">阻塞</div>
                  <div className="text-2xl font-bold text-red-600">
                    {boardData.summary.blocked || 0}
                  </div>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">已完成</div>
                  <div className="text-2xl font-bold text-emerald-600">
                    {boardData.summary.done || 0}
                  </div>
                </div>
                <CheckCircle2 className="w-8 h-8 text-emerald-500" />
              </div>
            </CardContent>
          </Card>
      </div>
      }
      {/* Kanban Board */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {boardData?.columns?.map((column) => {
          const tasks = column.tasks || [];
          const columnConfig = (statusColumns || []).find(
            (col) => col.key === column.status
          ) || { label: column.status_name, color: "bg-slate-200" };
          return (
            <Card key={column.status}>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>{column.status_name}</span>
                  <Badge className={columnConfig.color}>{tasks?.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {(tasks || []).map((task) =>
                  <div
                    key={task.id}
                    className="border rounded-lg p-3 hover:bg-slate-50 transition-colors cursor-pointer"
                    onClick={() =>
                    navigate(`/projects/${id}/tasks/${task.id}`)
                    }>

                      <div className="font-medium text-sm mb-2">
                        {task.task_name}
                      </div>
                      {task.stage &&
                    <Badge variant="outline" className="text-xs mb-2">
                          {task.stage}
                    </Badge>
                    }
                      {task.progress !== undefined &&
                    <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs text-slate-500">
                            <span>进度</span>
                            <span>{task.progress}%</span>
                          </div>
                          <Progress value={task.progress} className="h-1.5" />
                    </div>
                    }
                      {task.owner_name &&
                    <div className="text-xs text-slate-500 mt-2">
                          负责人: {task.owner_name}
                    </div>
                    }
                      {task.plan_end &&
                    <div className="text-xs text-slate-500 mt-1">
                          截止: {formatDate(task.plan_end)}
                    </div>
                    }
                  </div>
                  )}
                  {tasks?.length === 0 &&
                  <div className="text-center py-8 text-slate-400 text-sm">
                      暂无任务
                  </div>
                  }
                </div>
              </CardContent>
            </Card>);

        })}
      </div>
    </div>);

}
