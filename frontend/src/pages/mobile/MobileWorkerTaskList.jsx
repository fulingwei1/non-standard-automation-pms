/**
 * Mobile Worker Task List - 移动端工人任务列表
 * 功能：显示我的工单任务列表，支持快速操作
 */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  RefreshCw,
  Package,
  Clock,
  PlayCircle,
  CheckCircle2,
  AlertCircle,
  Filter } from
"lucide-react";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Progress } from "../../components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../../components/ui/select";
import { cn, formatDate as _formatDate } from "../../lib/utils";
import { productionApi } from "../../services/api";

const statusConfigs = {
  PENDING: { label: "待派工", color: "bg-slate-500" },
  ASSIGNED: { label: "待开工", color: "bg-blue-500" },
  STARTED: { label: "已开始", color: "bg-amber-500" },
  IN_PROGRESS: { label: "进行中", color: "bg-amber-500" },
  PAUSED: { label: "已暂停", color: "bg-purple-500" },
  COMPLETED: { label: "已完成", color: "bg-emerald-500" },
  CANCELLED: { label: "已取消", color: "bg-gray-500" }
};

export default function MobileWorkerTaskList() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [tasks, setTasks] = useState([]);
  const [filterStatus, setFilterStatus] = useState("");

  useEffect(() => {
    fetchTasks();
  }, [filterStatus]);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const params = { page: 1, page_size: 100 };
      const res = await productionApi.workOrders.list(params);
      const allOrders = res.data?.items || res.data?.items || res.data || [];

      // 筛选已派工的任务
      const myTasks = (allOrders || []).filter(
        (order) =>
        order.status === "ASSIGNED" ||
        order.status === "STARTED" ||
        order.status === "IN_PROGRESS" ||
        order.status === "PAUSED"
      );

      if (filterStatus) {
        const filtered = (myTasks || []).filter(
          (order) => order.status === filterStatus
        );
        setTasks(filtered);
      } else {
        setTasks(myTasks);
      }
    } catch (error) {
      console.error("Failed to fetch tasks:", error);
    } finally {
      setLoading(false);
    }
  };

  const stats = {
    total: tasks?.length,
    assigned: (tasks || []).filter((t) => t.status === "ASSIGNED").length,
    inProgress: (tasks || []).filter(
      (t) => t.status === "STARTED" || t.status === "IN_PROGRESS"
    ).length,
    completed: (tasks || []).filter((t) => t.status === "COMPLETED").length
  };

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      {/* 顶部导航栏 */}
      <div className="sticky top-0 z-10 bg-white border-b border-slate-200 shadow-sm">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(-1)}
              className="p-2">

              <ArrowLeft className="w-5 h-5" />
            </Button>
            <h1 className="text-lg font-semibold">我的任务</h1>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={fetchTasks}
              className="p-2">

              <RefreshCw className={cn("w-5 h-5", loading && "animate-spin")} />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/mobile/scan-start")}
              className="p-2">

              <PlayCircle className="w-5 h-5 text-blue-500" />
            </Button>
          </div>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 gap-3 p-4">
        <div className="bg-white rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-500">待开工</span>
            <Clock className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold text-blue-600">
            {stats.assigned}
          </div>
        </div>
        <div className="bg-white rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-500">进行中</span>
            <PlayCircle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-amber-600">
            {stats.inProgress}
          </div>
        </div>
      </div>

      {/* 筛选栏 */}
      <div className="px-4 mb-3">
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-full">
            <Filter className="w-4 h-4 mr-2" />
            <SelectValue placeholder="全部状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部状态</SelectItem>
            <SelectItem value="ASSIGNED">待开工</SelectItem>
            <SelectItem value="STARTED">已开始</SelectItem>
            <SelectItem value="IN_PROGRESS">进行中</SelectItem>
            <SelectItem value="PAUSED">已暂停</SelectItem>
            <SelectItem value="COMPLETED">已完成</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* 任务列表 */}
      <div className="px-4 space-y-3">
        {loading ?
        <div className="text-center py-12 text-slate-400">加载中...</div> :
        tasks?.length === 0 ?
        <div className="text-center py-12 text-slate-400">暂无任务</div> :

        (tasks || []).map((task) =>
        <div
          key={task.id}
          className="bg-white rounded-lg p-4 shadow-sm active:scale-[0.98] transition-transform"
          onClick={() => navigate(`/work-orders/${task.id}`)}>

              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge
                  className={
                  statusConfigs[task.status]?.color || "bg-slate-500"
                  }>

                      {statusConfigs[task.status]?.label || task.status}
                    </Badge>
                    <span className="font-mono text-xs text-slate-500">
                      {task.work_order_no}
                    </span>
                  </div>
                  <h3 className="font-medium text-base mb-1">
                    {task.task_name}
                  </h3>
                  <div className="text-sm text-slate-500">
                    {task.project_name || "-"} / {task.workshop_name || "-"}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-3 text-sm">
                <div>
                  <div className="text-slate-500 mb-1">计划数量</div>
                  <div className="font-medium">{task.plan_qty || 0}</div>
                </div>
                <div>
                  <div className="text-slate-500 mb-1">完成数量</div>
                  <div className="font-medium text-emerald-600">
                    {task.completed_qty || 0} / {task.plan_qty || 0}
                  </div>
                </div>
              </div>

              {task.progress !== undefined &&
          <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">进度</span>
                    <span className="font-medium">{task.progress}%</span>
                  </div>
                  <Progress value={task.progress} className="h-2" />
          </div>
          }

              {/* 操作按钮 */}
              <div className="flex gap-2 mt-3 pt-3 border-t border-slate-100">
                {task.status === "ASSIGNED" &&
            <Button
              size="sm"
              className="flex-1 bg-blue-500 hover:bg-blue-600"
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/mobile/scan-start?workOrderId=${task.id}`);
              }}>

                    <PlayCircle className="w-4 h-4 mr-1" />
                    开工
            </Button>
            }
                {(task.status === "STARTED" ||
            task.status === "IN_PROGRESS" ||
            task.status === "PAUSED") &&
            <>
                    <Button
                size="sm"
                variant="outline"
                className="flex-1"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(
                    `/mobile/progress-report?workOrderId=${task.id}`
                  );
                }}>

                      报进度
                    </Button>
                    <Button
                size="sm"
                className="flex-1 bg-emerald-500 hover:bg-emerald-600"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(
                    `/mobile/complete-report?workOrderId=${task.id}`
                  );
                }}>

                      完工
                    </Button>
            </>
            }
              </div>
        </div>
        )
        }
      </div>
    </div>);

}