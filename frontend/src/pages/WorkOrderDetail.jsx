/**
 * Work Order Detail Page - 工单详情页面
 * Features: 工单详情、进度跟踪、报工记录
 */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Package,
  Clock,
  User,
  TrendingUp,
  CheckCircle2,
  AlertTriangle,
  Calendar,
  FileText,
  RefreshCw } from
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
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger } from
"../components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../components/ui/table";
import { cn as _cn, formatDate } from "../lib/utils";
import { productionApi } from "../services/api";
const statusConfigs = {
  PENDING: { label: "待派工", color: "bg-slate-500" },
  ASSIGNED: { label: "已派工", color: "bg-blue-500" },
  STARTED: { label: "已开始", color: "bg-amber-500" },
  IN_PROGRESS: { label: "进行中", color: "bg-amber-500" },
  PAUSED: { label: "已暂停", color: "bg-purple-500" },
  COMPLETED: { label: "已完成", color: "bg-emerald-500" },
  CANCELLED: { label: "已取消", color: "bg-gray-500" }
};
const reportTypeConfigs = {
  START: { label: "开工", color: "bg-blue-500" },
  PROGRESS: { label: "进度", color: "bg-amber-500" },
  COMPLETE: { label: "完工", color: "bg-emerald-500" }
};
export default function WorkOrderDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [workOrder, setWorkOrder] = useState(null);
  const [workReports, setWorkReports] = useState([]);
  useEffect(() => {
    if (id) {
      fetchWorkOrderDetail();
      fetchWorkReports();
    }
  }, [id]);
  const fetchWorkOrderDetail = async () => {
    try {
      setLoading(true);
      const res = await productionApi.workOrders.get(id);
      setWorkOrder(res.data || res);
    } catch (error) {
      console.error("Failed to fetch work order detail:", error);
    } finally {
      setLoading(false);
    }
  };
  const fetchWorkReports = async () => {
    try {
      const res = await productionApi.workOrders.getReports(id);
      const reportList = res.data?.items || res.data?.reports || res.data || [];
      setWorkReports(reportList);
    } catch (error) {
      console.error("Failed to fetch work reports:", error);
    }
  };
  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">加载中...</div>
      </div>);

  }
  if (!workOrder) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">工单不存在</div>
      </div>);

  }
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate("/work-orders")}>

            <ArrowLeft className="w-4 h-4 mr-2" />
            返回列表
          </Button>
          <PageHeader
            title={`工单详情 - ${workOrder.work_order_no || workOrder.task_name}`}
            description="工单详情、进度跟踪、报工记录" />

        </div>
        <Button variant="outline" onClick={fetchWorkOrderDetail}>
          <RefreshCw className="w-4 h-4 mr-2" />
          刷新
        </Button>
      </div>
      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle>基本信息</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-slate-500 mb-1">工单编号</div>
              <div className="font-mono font-medium">
                {workOrder.work_order_no}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">任务名称</div>
              <div className="font-medium">{workOrder.task_name}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">状态</div>
              <Badge
                className={
                statusConfigs[workOrder.status]?.color || "bg-slate-500"
                }>

                {statusConfigs[workOrder.status]?.label || workOrder.status}
              </Badge>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">优先级</div>
              <Badge variant="outline">{workOrder.priority || "-"}</Badge>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">项目</div>
              <div>{workOrder.project_name || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">机台</div>
              <div>{workOrder.machine_name || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">车间</div>
              <div>{workOrder.workshop_name || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">工位</div>
              <div>{workOrder.workstation_name || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">物料</div>
              <div>{workOrder.material_name || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">工序</div>
              <div>{workOrder.process_name || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">分配工人</div>
              <div>{workOrder.assigned_worker_name || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">计划数量</div>
              <div className="font-medium">{workOrder.plan_qty || 0}</div>
            </div>
          </div>
        </CardContent>
      </Card>
      {/* Progress & Quantity */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>进度</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold">
                  {workOrder.progress || 0}%
                </span>
              </div>
              <Progress value={workOrder.progress || 0} className="h-3" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>完成数量</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold text-emerald-600">
                  {workOrder.completed_qty || 0}
                </span>
                <span className="text-slate-500">
                  / {workOrder.plan_qty || 0}
                </span>
              </div>
              <Progress
                value={
                workOrder.plan_qty ?
                workOrder.completed_qty / workOrder.plan_qty * 100 :
                0
                }
                className="h-3" />

            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>合格数量</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold text-blue-600">
                  {workOrder.qualified_qty || 0}
                </span>
                {workOrder.completed_qty > 0 &&
                <span className="text-slate-500">
                    合格率:{" "}
                    {(
                  workOrder.qualified_qty / workOrder.completed_qty *
                  100).
                  toFixed(1)}
                    %
                </span>
                }
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      {/* Time & Hours */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">计划开始</div>
                <div className="text-sm">
                  {workOrder.plan_start_date ?
                  formatDate(workOrder.plan_start_date) :
                  "-"}
                </div>
              </div>
              <Calendar className="w-5 h-5 text-slate-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">计划结束</div>
                <div className="text-sm">
                  {workOrder.plan_end_date ?
                  formatDate(workOrder.plan_end_date) :
                  "-"}
                </div>
              </div>
              <Calendar className="w-5 h-5 text-slate-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">标准工时</div>
                <div className="text-sm font-medium">
                  {workOrder.standard_hours ?
                  `${workOrder.standard_hours}h` :
                  "-"}
                </div>
              </div>
              <Clock className="w-5 h-5 text-slate-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">实际工时</div>
                <div className="text-sm font-medium">
                  {workOrder.actual_hours ?
                  `${workOrder.actual_hours.toFixed(1)}h` :
                  "-"}
                </div>
              </div>
              <Clock className="w-5 h-5 text-slate-400" />
            </div>
          </CardContent>
        </Card>
      </div>
      {/* Tabs: Reports & Details */}
      <Card>
        <CardContent className="pt-6">
          <Tabs defaultValue="reports" className="w-full">
            <TabsList>
              <TabsTrigger value="reports">报工记录</TabsTrigger>
              <TabsTrigger value="details">详细信息</TabsTrigger>
            </TabsList>
            <TabsContent value="reports" className="mt-4">
              {workReports.length === 0 ?
              <div className="text-center py-8 text-slate-400">
                  暂无报工记录
              </div> :

              <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>报工单号</TableHead>
                      <TableHead>报工类型</TableHead>
                      <TableHead>工人</TableHead>
                      <TableHead>报工时间</TableHead>
                      <TableHead>进度</TableHead>
                      <TableHead>完成数量</TableHead>
                      <TableHead>合格数量</TableHead>
                      <TableHead>工时</TableHead>
                      <TableHead>状态</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {workReports.map((report) =>
                  <TableRow key={report.id}>
                        <TableCell className="font-mono text-sm">
                          {report.report_no}
                        </TableCell>
                        <TableCell>
                          <Badge
                        className={
                        reportTypeConfigs[report.report_type]?.color ||
                        "bg-slate-500"
                        }>

                            {reportTypeConfigs[report.report_type]?.label ||
                        report.report_type}
                          </Badge>
                        </TableCell>
                        <TableCell>{report.worker_name || "-"}</TableCell>
                        <TableCell className="text-slate-500 text-sm">
                          {report.report_time ?
                      formatDate(report.report_time) :
                      "-"}
                        </TableCell>
                        <TableCell>
                          {report.progress_percent !== undefined ?
                      `${report.progress_percent}%` :
                      "-"}
                        </TableCell>
                        <TableCell>{report.completed_qty || 0}</TableCell>
                        <TableCell className="text-emerald-600">
                          {report.qualified_qty || 0}
                        </TableCell>
                        <TableCell>
                          {report.work_hours ?
                      `${report.work_hours.toFixed(1)}h` :
                      "-"}
                        </TableCell>
                        <TableCell>
                          <Badge
                        variant={
                        report.status === "APPROVED" ?
                        "default" :
                        "outline"
                        }>

                            {report.status === "APPROVED" ? "已审批" : "待审批"}
                          </Badge>
                        </TableCell>
                  </TableRow>
                  )}
                  </TableBody>
              </Table>
              }
            </TabsContent>
            <TabsContent value="details" className="mt-4">
              <div className="space-y-4">
                <div>
                  <div className="text-sm font-medium mb-2">工作内容</div>
                  <div className="text-slate-600">
                    {workOrder.work_content || "-"}
                  </div>
                </div>
                {workOrder.drawing_no &&
                <div>
                    <div className="text-sm font-medium mb-2">图纸编号</div>
                    <div className="font-mono">{workOrder.drawing_no}</div>
                </div>
                }
                {workOrder.remark &&
                <div>
                    <div className="text-sm font-medium mb-2">备注</div>
                    <div className="text-slate-600">{workOrder.remark}</div>
                </div>
                }
                {workOrder.actual_start_time &&
                <div>
                    <div className="text-sm font-medium mb-2">实际开始时间</div>
                    <div>{formatDate(workOrder.actual_start_time)}</div>
                </div>
                }
                {workOrder.actual_end_time &&
                <div>
                    <div className="text-sm font-medium mb-2">实际结束时间</div>
                    <div>{formatDate(workOrder.actual_end_time)}</div>
                </div>
                }
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>);

}