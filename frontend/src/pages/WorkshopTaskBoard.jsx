/**
 * Workshop Task Board Page - 车间任务看板页面
 * Features: 拖拽式看板，按状态展示工单，支持工位状态监控
 */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  RefreshCw,
  Wrench,
  CheckCircle2,
  Clock,
  User,
  Package,
  TrendingUp,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { cn, formatDate } from "../lib/utils";
import { productionApi } from "../services/api";
const workstationStatusConfigs = {
  IDLE: { label: "空闲", color: "bg-emerald-500" },
  WORKING: { label: "工作中", color: "bg-blue-500" },
  MAINTENANCE: { label: "保养中", color: "bg-amber-500" },
  FAULT: { label: "故障", color: "bg-red-500" },
};
export default function WorkshopTaskBoard() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [boardData, setBoardData] = useState(null);
  const workshopId = id ? parseInt(id, 10) : null;

  useEffect(() => {
    if (workshopId) {
      fetchBoardData();
    }
  }, [workshopId]);

  const fetchBoardData = async () => {
    try {
      setLoading(true);
      if (!workshopId) {return;}
      const res = await productionApi.taskBoard(workshopId);
      setBoardData(res.data || res);
    } catch (error) {
      console.error("Failed to fetch board data:", error);
    } finally {
      setLoading(false);
    }
  };
  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">加载中...</div>
      </div>
    );
  }
  if (!boardData) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">暂无数据</div>
      </div>
    );
  }
  // Group work orders by status
  const ordersByStatus = {
    pending:
      boardData.work_orders?.filter((wo) => wo.status === "PENDING") || [],
    assigned:
      boardData.work_orders?.filter((wo) => wo.status === "ASSIGNED") || [],
    in_progress:
      boardData.work_orders?.filter(
        (wo) => wo.status === "IN_PROGRESS" || wo.status === "STARTED",
      ) || [],
    paused: boardData.work_orders?.filter((wo) => wo.status === "PAUSED") || [],
    completed:
      boardData.work_orders?.filter((wo) => wo.status === "COMPLETED") || [],
  };
  const columns = [
    { key: "pending", title: "待派工", orders: ordersByStatus.pending },
    { key: "assigned", title: "已派工", orders: ordersByStatus.assigned },
    { key: "in_progress", title: "进行中", orders: ordersByStatus.in_progress },
    { key: "paused", title: "已暂停", orders: ordersByStatus.paused },
    { key: "completed", title: "已完成", orders: ordersByStatus.completed },
  ];
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate("/production-dashboard")}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回驾驶舱
          </Button>
          <PageHeader
            title={`${boardData.workshop_name || "车间"} - 任务看板`}
            description="拖拽式看板，实时监控工单状态和工位情况"
          />
        </div>
        <Button variant="outline" onClick={fetchBoardData}>
          <RefreshCw className="w-4 h-4 mr-2" />
          刷新
        </Button>
      </div>
      {/* Workshop Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">工位总数</div>
                <div className="text-2xl font-bold">
                  {boardData.workstations?.length || 0}
                </div>
              </div>
              <Wrench className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">工单总数</div>
                <div className="text-2xl font-bold">
                  {boardData.work_orders?.length || 0}
                </div>
              </div>
              <Package className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">进行中</div>
                <div className="text-2xl font-bold text-amber-600">
                  {ordersByStatus.in_progress.length}
                </div>
              </div>
              <TrendingUp className="w-8 h-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">已完成</div>
                <div className="text-2xl font-bold text-emerald-600">
                  {ordersByStatus.completed.length}
                </div>
              </div>
              <CheckCircle2 className="w-8 h-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
      </div>
      {/* Workstation Status */}
      {boardData.workstations && boardData.workstations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>工位状态</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {boardData.workstations.map((ws) => (
                <div
                  key={ws.id}
                  className={cn(
                    "border rounded-lg p-3 text-center",
                    ws.status === "WORKING" && "bg-blue-50 border-blue-200",
                    ws.status === "IDLE" && "bg-emerald-50 border-emerald-200",
                    ws.status === "MAINTENANCE" &&
                      "bg-amber-50 border-amber-200",
                    ws.status === "FAULT" && "bg-red-50 border-red-200",
                  )}
                >
                  <div className="font-medium text-sm mb-1">
                    {ws.workstation_name}
                  </div>
                  <Badge
                    className={
                      workstationStatusConfigs[ws.status]?.color ||
                      "bg-slate-500"
                    }
                  >
                    {workstationStatusConfigs[ws.status]?.label || ws.status}
                  </Badge>
                  {ws.current_worker_name && (
                    <div className="text-xs text-slate-500 mt-2">
                      <User className="w-3 h-3 inline mr-1" />
                      {ws.current_worker_name}
                    </div>
                  )}
                  {ws.current_work_order_no && (
                    <div className="text-xs text-slate-500 mt-1 font-mono">
                      {ws.current_work_order_no}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      {/* Kanban Board */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {columns.map((column) => (
          <Card key={column.key}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>{column.title}</span>
                <Badge variant="outline">{column.orders.length}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 min-h-[400px]">
                {column.orders.map((order) => (
                  <div
                    key={order.id}
                    className="border rounded-lg p-3 hover:bg-slate-50 transition-colors cursor-pointer"
                    onClick={() => navigate(`/work-orders/${order.id}`)}
                  >
                    <div className="font-medium text-sm mb-2">
                      {order.task_name}
                    </div>
                    <div className="text-xs text-slate-500 mb-2 font-mono">
                      {order.work_order_no}
                    </div>
                    {order.project_name && (
                      <div className="text-xs text-slate-500 mb-2">
                        项目: {order.project_name}
                      </div>
                    )}
                    {order.material_name && (
                      <div className="text-xs text-slate-500 mb-2">
                        物料: {order.material_name}
                      </div>
                    )}
                    <div className="flex items-center justify-between text-xs mb-2">
                      <span>计划: {order.plan_qty || 0}</span>
                      <span className="font-medium">
                        完成: {order.completed_qty || 0}
                      </span>
                    </div>
                    {order.progress !== undefined && (
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span>进度</span>
                          <span>{order.progress}%</span>
                        </div>
                        <Progress value={order.progress} className="h-1.5" />
                      </div>
                    )}
                    {order.assigned_worker_name && (
                      <div className="text-xs text-slate-500 mt-2 flex items-center gap-1">
                        <User className="w-3 h-3" />
                        {order.assigned_worker_name}
                      </div>
                    )}
                    {order.plan_start_date && (
                      <div className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDate(order.plan_start_date)}
                        {order.plan_end_date && (
                          <>
                            <span className="mx-1">-</span>
                            {formatDate(order.plan_end_date)}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                ))}
                {column.orders.length === 0 && (
                  <div className="text-center py-8 text-slate-400 text-sm">
                    暂无工单
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
