/**
 * Outsourcing Order Detail Page - 外协订单详情页面
 * Features: 外协订单详情、进度跟踪、质检记录
 */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Package,
  Clock,
  CheckCircle2,
  XCircle,
  TrendingUp,
  RefreshCw,
  Calendar,
  FileText,
  Factory,
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
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { cn, formatDate, formatCurrency } from "../lib/utils";
import { outsourcingApi } from "../services/api";
const statusConfigs = {
  DRAFT: { label: "草稿", color: "bg-slate-500" },
  SUBMITTED: { label: "已提交", color: "bg-blue-500" },
  APPROVED: { label: "已批准", color: "bg-emerald-500" },
  IN_PROGRESS: { label: "进行中", color: "bg-amber-500" },
  DELIVERED: { label: "已交付", color: "bg-purple-500" },
  INSPECTED: { label: "已质检", color: "bg-violet-500" },
  COMPLETED: { label: "已完成", color: "bg-green-500" },
  CANCELLED: { label: "已取消", color: "bg-gray-500" },
};
const inspectResultConfigs = {
  PASSED: { label: "合格", color: "bg-emerald-500" },
  FAILED: { label: "不合格", color: "bg-red-500" },
  CONDITIONAL: { label: "有条件合格", color: "bg-amber-500" },
};
export default function OutsourcingOrderDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [order, setOrder] = useState(null);
  const [deliveries, setDeliveries] = useState([]);
  const [inspections, setInspections] = useState([]);
  const [progressLogs, setProgressLogs] = useState([]);
  useEffect(() => {
    if (id) {
      fetchOrderDetail();
      fetchDeliveries();
      fetchInspections();
      fetchProgressLogs();
    }
  }, [id]);
  const fetchOrderDetail = async () => {
    try {
      setLoading(true);
      const res = await outsourcingApi.orders.get(id);
      setOrder(res.data || res);
    } catch (error) {
      console.error("Failed to fetch order detail:", error);
    } finally {
      setLoading(false);
    }
  };
  const fetchDeliveries = async () => {
    try {
      const res = await outsourcingApi.orders.getDeliveries(id);
      const deliveryList = res.data?.items || res.data || [];
      setDeliveries(deliveryList);
    } catch (error) {
      console.error("Failed to fetch deliveries:", error);
    }
  };
  const fetchInspections = async () => {
    try {
      const res = await outsourcingApi.orders.getInspections(id);
      const inspectionList = res.data?.items || res.data || [];
      setInspections(inspectionList);
    } catch (error) {
      console.error("Failed to fetch inspections:", error);
    }
  };
  const fetchProgressLogs = async () => {
    try {
      const res = await outsourcingApi.orders.getProgress(id);
      const progressList = res.data || res || [];
      setProgressLogs(progressList);
    } catch (error) {
      console.error("Failed to fetch progress logs:", error);
    }
  };
  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">加载中...</div>
      </div>
    );
  }
  if (!order) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">订单不存在</div>
      </div>
    );
  }
  // Calculate statistics
  const totalQuantity =
    order.items?.reduce(
      (sum, item) => sum + (parseFloat(item.quantity) || 0),
      0,
    ) || 0;
  const deliveredQuantity =
    order.items?.reduce(
      (sum, item) => sum + (parseFloat(item.delivered_quantity) || 0),
      0,
    ) || 0;
  const qualifiedQuantity =
    order.items?.reduce(
      (sum, item) => sum + (parseFloat(item.qualified_quantity) || 0),
      0,
    ) || 0;
  const rejectedQuantity =
    order.items?.reduce(
      (sum, item) => sum + (parseFloat(item.rejected_quantity) || 0),
      0,
    ) || 0;
  const deliveryRate =
    totalQuantity > 0 ? (deliveredQuantity / totalQuantity) * 100 : 0;
  const passRate =
    deliveredQuantity > 0 ? (qualifiedQuantity / deliveredQuantity) * 100 : 0;
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate("/outsourcing-orders")}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回列表
          </Button>
          <PageHeader
            title={`外协订单详情 - ${order.order_no}`}
            description="外协订单详情、进度跟踪、质检记录"
          />
        </div>
        <Button variant="outline" onClick={fetchOrderDetail}>
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
              <div className="text-sm text-slate-500 mb-1">订单编号</div>
              <div className="font-mono font-medium">{order.order_no}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">订单标题</div>
              <div className="font-medium">{order.order_title}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">状态</div>
              <Badge
                className={statusConfigs[order.status]?.color || "bg-slate-500"}
              >
                {statusConfigs[order.status]?.label || order.status}
              </Badge>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">付款状态</div>
              <Badge variant="outline">{order.payment_status || "-"}</Badge>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">外协商</div>
              <div>{order.vendor_name || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">项目</div>
              <div>{order.project_name || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">机台</div>
              <div>{order.machine_name || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">订单类型</div>
              <div>{order.order_type || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">订单金额</div>
              <div className="font-medium text-emerald-600">
                {formatCurrency(order.amount_with_tax || 0)}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">已付金额</div>
              <div className="font-medium">
                {formatCurrency(order.paid_amount || 0)}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">要求日期</div>
              <div>
                {order.required_date ? formatDate(order.required_date) : "-"}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">预计日期</div>
              <div>
                {order.estimated_date ? formatDate(order.estimated_date) : "-"}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">交付率</div>
                <div className="text-2xl font-bold">
                  {deliveryRate.toFixed(1)}%
                </div>
              </div>
              <Package className="w-8 h-8 text-blue-500" />
            </div>
            <Progress value={deliveryRate} className="mt-2 h-2" />
            <div className="text-xs text-slate-500 mt-1">
              {deliveredQuantity} / {totalQuantity}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">合格率</div>
                <div className="text-2xl font-bold text-emerald-600">
                  {passRate.toFixed(1)}%
                </div>
              </div>
              <CheckCircle2 className="w-8 h-8 text-emerald-500" />
            </div>
            <Progress value={passRate} className="mt-2 h-2" />
            <div className="text-xs text-slate-500 mt-1">
              合格: {qualifiedQuantity} | 不合格: {rejectedQuantity}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">交付次数</div>
                <div className="text-2xl font-bold">{deliveries.length}</div>
              </div>
              <Factory className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">质检次数</div>
                <div className="text-2xl font-bold">{inspections.length}</div>
              </div>
              <CheckCircle2 className="w-8 h-8 text-violet-500" />
            </div>
          </CardContent>
        </Card>
      </div>
      {/* Tabs: Items, Deliveries, Inspections, Progress */}
      <Card>
        <CardContent className="pt-6">
          <Tabs defaultValue="items" className="w-full">
            <TabsList>
              <TabsTrigger value="items">订单明细</TabsTrigger>
              <TabsTrigger value="deliveries">交付记录</TabsTrigger>
              <TabsTrigger value="inspections">质检记录</TabsTrigger>
              <TabsTrigger value="progress">进度记录</TabsTrigger>
            </TabsList>
            <TabsContent value="items" className="mt-4">
              {order.items && order.items.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>序号</TableHead>
                      <TableHead>物料编码</TableHead>
                      <TableHead>物料名称</TableHead>
                      <TableHead>规格</TableHead>
                      <TableHead>工艺类型</TableHead>
                      <TableHead>数量</TableHead>
                      <TableHead>单价</TableHead>
                      <TableHead>金额</TableHead>
                      <TableHead>已交付</TableHead>
                      <TableHead>合格</TableHead>
                      <TableHead>不合格</TableHead>
                      <TableHead>状态</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {order.items.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell>{item.item_no}</TableCell>
                        <TableCell className="font-mono text-sm">
                          {item.material_code}
                        </TableCell>
                        <TableCell className="font-medium">
                          {item.material_name}
                        </TableCell>
                        <TableCell>{item.specification || "-"}</TableCell>
                        <TableCell>{item.process_type || "-"}</TableCell>
                        <TableCell>{item.quantity}</TableCell>
                        <TableCell>
                          {formatCurrency(item.unit_price || 0)}
                        </TableCell>
                        <TableCell className="font-medium">
                          {formatCurrency(item.amount || 0)}
                        </TableCell>
                        <TableCell>
                          <span
                            className={
                              parseFloat(item.delivered_quantity || 0) >=
                              parseFloat(item.quantity || 0)
                                ? "text-emerald-600"
                                : ""
                            }
                          >
                            {item.delivered_quantity || 0}
                          </span>
                        </TableCell>
                        <TableCell className="text-emerald-600">
                          {item.qualified_quantity || 0}
                        </TableCell>
                        <TableCell className="text-red-600">
                          {item.rejected_quantity || 0}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{item.status || "-"}</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-slate-400">
                  暂无订单明细
                </div>
              )}
            </TabsContent>
            <TabsContent value="deliveries" className="mt-4">
              {deliveries.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  暂无交付记录
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>交付单号</TableHead>
                      <TableHead>交付日期</TableHead>
                      <TableHead>交付类型</TableHead>
                      <TableHead>交付人</TableHead>
                      <TableHead>物流公司</TableHead>
                      <TableHead>运单号</TableHead>
                      <TableHead>状态</TableHead>
                      <TableHead>收货时间</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {deliveries.map((delivery) => (
                      <TableRow key={delivery.id}>
                        <TableCell className="font-mono text-sm">
                          {delivery.delivery_no}
                        </TableCell>
                        <TableCell>
                          {formatDate(delivery.delivery_date)}
                        </TableCell>
                        <TableCell>{delivery.delivery_type || "-"}</TableCell>
                        <TableCell>{delivery.delivery_person || "-"}</TableCell>
                        <TableCell>
                          {delivery.logistics_company || "-"}
                        </TableCell>
                        <TableCell className="font-mono text-sm">
                          {delivery.tracking_no || "-"}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              delivery.status === "RECEIVED"
                                ? "default"
                                : "outline"
                            }
                          >
                            {delivery.status === "RECEIVED"
                              ? "已收货"
                              : "待收货"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-slate-500 text-sm">
                          {delivery.received_at
                            ? formatDate(delivery.received_at)
                            : "-"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </TabsContent>
            <TabsContent value="inspections" className="mt-4">
              {inspections.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  暂无质检记录
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>质检单号</TableHead>
                      <TableHead>质检日期</TableHead>
                      <TableHead>质检类型</TableHead>
                      <TableHead>质检员</TableHead>
                      <TableHead>送检数量</TableHead>
                      <TableHead>合格数量</TableHead>
                      <TableHead>不合格数量</TableHead>
                      <TableHead>合格率</TableHead>
                      <TableHead>质检结果</TableHead>
                      <TableHead>处置方式</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {inspections.map((inspection) => (
                      <TableRow key={inspection.id}>
                        <TableCell className="font-mono text-sm">
                          {inspection.inspection_no}
                        </TableCell>
                        <TableCell>
                          {formatDate(inspection.inspect_date)}
                        </TableCell>
                        <TableCell>{inspection.inspect_type || "-"}</TableCell>
                        <TableCell>
                          {inspection.inspector_name || "-"}
                        </TableCell>
                        <TableCell>
                          {inspection.inspect_quantity || 0}
                        </TableCell>
                        <TableCell className="text-emerald-600">
                          {inspection.qualified_quantity || 0}
                        </TableCell>
                        <TableCell className="text-red-600">
                          {inspection.rejected_quantity || 0}
                        </TableCell>
                        <TableCell>
                          <span
                            className={
                              inspection.pass_rate >= 95
                                ? "text-emerald-600"
                                : inspection.pass_rate >= 80
                                  ? "text-amber-600"
                                  : "text-red-600"
                            }
                          >
                            {inspection.pass_rate?.toFixed(1) || 0}%
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge
                            className={
                              inspectResultConfigs[inspection.inspect_result]
                                ?.color || "bg-slate-500"
                            }
                          >
                            {inspectResultConfigs[inspection.inspect_result]
                              ?.label || inspection.inspect_result}
                          </Badge>
                        </TableCell>
                        <TableCell>{inspection.disposition || "-"}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </TabsContent>
            <TabsContent value="progress" className="mt-4">
              {progressLogs.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  暂无进度记录
                </div>
              ) : (
                <div className="space-y-4">
                  {progressLogs.map((progress) => (
                    <Card key={progress.id}>
                      <CardContent className="pt-4">
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <div className="font-medium">
                              {formatDate(progress.report_date)}
                            </div>
                            <div className="text-sm text-slate-500 mt-1">
                              当前工序: {progress.current_process || "-"}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold text-blue-600">
                              {progress.progress_pct || 0}%
                            </div>
                            <Progress
                              value={progress.progress_pct || 0}
                              className="mt-2 w-24"
                            />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4 mt-3">
                          <div>
                            <div className="text-sm text-slate-500">
                              完成数量
                            </div>
                            <div className="font-medium">
                              {progress.completed_quantity || 0}
                            </div>
                          </div>
                          <div>
                            <div className="text-sm text-slate-500">
                              预计完成
                            </div>
                            <div className="font-medium">
                              {progress.estimated_complete
                                ? formatDate(progress.estimated_complete)
                                : "-"}
                            </div>
                          </div>
                        </div>
                        {progress.issues && (
                          <div className="mt-3 p-3 bg-amber-50 rounded-lg">
                            <div className="text-sm font-medium text-amber-800 mb-1">
                              问题/风险
                            </div>
                            <div className="text-sm text-amber-700">
                              {progress.issues}
                            </div>
                          </div>
                        )}
                        {progress.risk_level && (
                          <div className="mt-2">
                            <Badge
                              className={cn(
                                progress.risk_level === "HIGH" && "bg-red-500",
                                progress.risk_level === "MEDIUM" &&
                                  "bg-amber-500",
                                progress.risk_level === "LOW" && "bg-blue-500",
                                "bg-slate-500",
                              )}
                            >
                              {progress.risk_level === "HIGH"
                                ? "高风险"
                                : progress.risk_level === "MEDIUM"
                                  ? "中风险"
                                  : progress.risk_level === "LOW"
                                    ? "低风险"
                                    : progress.risk_level}
                            </Badge>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
