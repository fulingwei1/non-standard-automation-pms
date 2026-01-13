/**
 * Material Readiness - 齐套管理
 * 统一管理物料齐套检查（工单级别）和齐套分析（项目级别）
 */

import { useState, useEffect, useCallback, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Package,
  CheckCircle2,
  AlertTriangle,
  Clock,
  RefreshCw,
  Search,
  Filter,
  Eye,
  Play,
  Calendar,
  TrendingUp,
  TrendingDown,
  Truck,
  Box,
  BarChart3,
  PieChart,
  LineChart,
  Download,
  Wrench,
  Zap,
  Cable,
  Bug,
  Palette,
  PlayCircle,
  PauseCircle,
  ExternalLink,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { cn, formatDate } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import {
  projectApi,
  bomApi,
  purchaseApi,
  assemblyKitApi,
  kitCheckApi,
} from "../services/api";
import {
  SimpleBarChart,
  SimplePieChart,
  SimpleLineChart,
} from "../components/administrative/StatisticsCharts";

// ===== Shared Configs =====
const kitStatusConfigs = {
  complete: {
    label: "完全齐套",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
  },
  partial: {
    label: "部分齐套",
    color: "bg-amber-500",
    textColor: "text-amber-400",
  },
  shortage: { label: "缺料", color: "bg-red-500", textColor: "text-red-400" },
};

const statusConfigs = {
  arrived: {
    label: "已到货",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
  },
  in_transit: {
    label: "在途",
    color: "bg-blue-500",
    textColor: "text-blue-400",
  },
  delayed: { label: "延期", color: "bg-red-500", textColor: "text-red-400" },
  not_ordered: {
    label: "未下单",
    color: "bg-amber-500",
    textColor: "text-amber-400",
  },
};

const impactConfigs = {
  high: { label: "高", color: "bg-red-500/20 text-red-400 border-red-500/30" },
  medium: {
    label: "中",
    color: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  },
  low: {
    label: "低",
    color: "bg-slate-500/20 text-slate-400 border-slate-500/30",
  },
};

// ===== KitCheck Tab Component =====
function KitCheckTab() {
  const [loading, setLoading] = useState(false);
  const [workOrders, setWorkOrders] = useState([]);
  const [summary, setSummary] = useState({
    total: 0,
    complete: 0,
    partial: 0,
    shortage: 0,
  });
  const [filters, setFilters] = useState({
    kit_status: "all",
    workshop_id: "",
    project_id: "",
    plan_date: "",
    keyword: "",
  });
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [selectedWorkOrder, setSelectedWorkOrder] = useState(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [detailData, setDetailData] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadWorkOrders();
  }, [page, filters]);

  const loadWorkOrders = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
      };
      if (filters.kit_status && filters.kit_status !== "all") {
        params.kit_status = filters.kit_status;
      }
      if (filters.workshop_id) {
        params.workshop_id = filters.workshop_id;
      }
      if (filters.project_id) {
        params.project_id = filters.project_id;
      }
      if (filters.plan_date) {
        params.plan_date = filters.plan_date;
      }
      if (filters.keyword) {
        params.keyword = filters.keyword;
      }
      const res = await kitCheckApi.list(params);
      const responseData = res.data?.data || res.data;
      if (res.data?.code === 200 || res.status === 200) {
        setWorkOrders(responseData?.work_orders || []);
        setSummary(responseData?.summary || { total: 0, complete: 0, partial: 0, shortage: 0 });
        setTotal(responseData?.pagination?.total || 0);
      } else {
        console.warn("Unexpected API response:", res.data);
        setWorkOrders([]);
        setSummary({ total: 0, complete: 0, partial: 0, shortage: 0 });
      }
    } catch (error) {
      console.error("加载工单列表失败", error);
    } finally {
      setLoading(false);
    }
  };

  const loadWorkOrderDetail = async (workOrderId) => {
    setDetailLoading(true);
    try {
      const res = await kitCheckApi.get(workOrderId);
      const responseData = res.data?.data || res.data;
      if (res.data?.code === 200 || res.status === 200) {
        setDetailData(responseData);
      }
    } catch (error) {
      console.error("加载工单详情失败", error);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleViewDetail = async (workOrder) => {
    setSelectedWorkOrder(workOrder);
    setShowDetailDialog(true);
    await loadWorkOrderDetail(workOrder.id);
  };

  const handleCheckKit = async (workOrderId) => {
    setActionLoading(true);
    try {
      // TODO: 实现具体的齐套检查逻辑
      alert("齐套检查功能开发中");
      // await kitCheckApi.check(workOrderId);
      if (selectedWorkOrder && selectedWorkOrder.id === workOrderId) {
        await loadWorkOrderDetail(workOrderId);
      }
      await loadWorkOrders();
    } catch (error) {
      console.error("执行齐套检查失败", error);
      alert("检查失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setActionLoading(false);
    }
  };

  const handleConfirmStart = async (workOrderId, confirmType = "start_now") => {
    if (!confirm(`确认工单物料齐套，可以开工吗？`)) return;

    setActionLoading(true);
    try {
      // TODO: 实现具体的确认开工逻辑
      alert("开工确认功能开发中");
      // await kitCheckApi.confirm(workOrderId, { confirm_type: confirmType, confirm_note: "确认开工" });
      setShowDetailDialog(false);
      await loadWorkOrders();
    } catch (error) {
      console.error("确认开工失败", error);
      alert("确认失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setActionLoading(false);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters((prev) => ({ ...prev, [field]: value }));
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* 统计卡片 */}
      <motion.div
        variants={fadeIn}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 md:grid-cols-4 gap-4"
      >
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">今日工单</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.total}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">完全齐套</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-400">
              {summary.complete}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">部分齐套</CardTitle>
            <AlertTriangle className="h-4 w-4 text-amber-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-400">
              {summary.partial}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">缺料</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-400">
              {summary.shortage}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 筛选栏 */}
      <Card>
        <CardHeader>
          <CardTitle>筛选条件</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div>
              <Select
                value={filters.kit_status}
                onValueChange={(value) =>
                  handleFilterChange("kit_status", value)
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="齐套状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部状态</SelectItem>
                  <SelectItem value="complete">完全齐套</SelectItem>
                  <SelectItem value="partial">部分齐套</SelectItem>
                  <SelectItem value="shortage">缺料</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Input
                placeholder="搜索工单号、任务名称..."
                value={filters.keyword}
                onChange={(e) => handleFilterChange("keyword", e.target.value)}
              />
            </div>

            <div>
              <Input
                type="date"
                placeholder="计划开工日期"
                value={filters.plan_date}
                onChange={(e) =>
                  handleFilterChange("plan_date", e.target.value)
                }
              />
            </div>

            <div>
              <Button variant="outline" onClick={loadWorkOrders}>
                <RefreshCw className="h-4 w-4 mr-2" />
                刷新
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 工单列表 */}
      <Card>
        <CardHeader>
          <CardTitle>待检查工单</CardTitle>
          <CardDescription>未来7天内计划开工的工单</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-16">
              <div className="inline-block">
                <RefreshCw className="w-8 h-8 animate-spin text-slate-400 mb-4" />
                <div className="text-muted-foreground">加载工单列表中...</div>
              </div>
            </div>
          ) : workOrders.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              暂无待检查工单
            </div>
          ) : (
            <div className="space-y-3">
              {workOrders.map((wo) => {
                const status =
                  kitStatusConfigs[wo.kit_status] || kitStatusConfigs.shortage;
                return (
                  <div
                    key={wo.id}
                    className={cn(
                      "flex items-center justify-between p-4 rounded-lg border border-border hover:bg-surface-2 transition-colors",
                      wo.kit_status === "complete" && "bg-emerald-500/5",
                      wo.kit_status === "partial" && "bg-amber-500/5",
                      wo.kit_status === "shortage" && "bg-red-500/5",
                    )}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-medium">{wo.work_order_no}</span>
                        <Badge
                          variant="outline"
                          className={cn(status.color, "text-white")}
                        >
                          {status.label}
                        </Badge>
                        <span className="text-sm text-muted-foreground">
                          {wo.workshop_name}
                        </span>
                      </div>
                      <div className="text-sm font-medium mb-1">
                        {wo.task_name}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {wo.project_name} | 计划开工:{" "}
                        {wo.plan_start_date
                          ? formatDate(wo.plan_start_date)
                          : "-"}
                      </div>
                      <div className="flex items-center gap-4 mt-2">
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                            <div
                              className={cn(
                                "h-full transition-all",
                                wo.kit_status === "complete" &&
                                  "bg-emerald-500",
                                wo.kit_status === "partial" && "bg-amber-500",
                                wo.kit_status === "shortage" && "bg-red-500",
                              )}
                              style={{ width: `${wo.kit_rate}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium">
                            {wo.kit_rate}%
                          </span>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          齐套: {wo.fulfilled_items} | 缺料: {wo.shortage_items}{" "}
                          | 在途: {wo.in_transit_items}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewDetail(wo)}
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        查看详情
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleCheckKit(wo.id)}
                        disabled={actionLoading}
                      >
                        <RefreshCw className="h-4 w-4 mr-2" />
                        检查
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {total > pageSize && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <div className="text-sm text-muted-foreground">
                共 {total} 条记录，第 {page} / {Math.ceil(total / pageSize)} 页
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1 || loading}
                >
                  上一页
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setPage((p) => Math.min(Math.ceil(total / pageSize), p + 1))
                  }
                  disabled={page >= Math.ceil(total / pageSize) || loading}
                >
                  下一页
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>工单齐套详情</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {detailLoading ? (
              <div className="text-center py-8 text-muted-foreground">
                加载中...
              </div>
            ) : detailData ? (
              <div className="space-y-6">
                {/* 工单信息 */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-muted-foreground">工单号</div>
                    <div className="font-medium">
                      {detailData.work_order?.work_order_no}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">
                      任务名称
                    </div>
                    <div className="font-medium">
                      {detailData.work_order?.task_name}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">项目</div>
                    <div className="font-medium">
                      {detailData.work_order?.project_name}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">
                      计划开工日期
                    </div>
                    <div className="font-medium">
                      {detailData.work_order?.plan_start_date
                        ? formatDate(detailData.work_order.plan_start_date)
                        : "-"}
                    </div>
                  </div>
                </div>

                {/* 齐套统计 */}
                <div className="grid grid-cols-4 gap-4">
                  <Card>
                    <CardContent className="pt-4">
                      <div className="text-2xl font-bold">
                        {detailData.kit_data?.total_items || 0}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        物料总项
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-4">
                      <div className="text-2xl font-bold text-emerald-400">
                        {detailData.kit_data?.fulfilled_items || 0}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        已齐套
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-4">
                      <div className="text-2xl font-bold text-red-400">
                        {detailData.kit_data?.shortage_items || 0}
                      </div>
                      <div className="text-sm text-muted-foreground">缺料</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-4">
                      <div className="text-2xl font-bold">
                        {detailData.kit_data?.kit_rate || 0}%
                      </div>
                      <div className="text-sm text-muted-foreground">
                        齐套率
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* BOM明细 */}
                <div>
                  <div className="text-sm font-medium mb-3">BOM明细</div>
                  <div className="border rounded-lg overflow-hidden">
                    <div className="grid grid-cols-8 gap-2 p-2 bg-surface-2 text-sm font-medium">
                      <div>物料编码</div>
                      <div>物料名称</div>
                      <div>规格</div>
                      <div>需求</div>
                      <div>可用</div>
                      <div>在途</div>
                      <div>缺料</div>
                      <div>状态</div>
                    </div>
                    {detailData.bom_items?.map((item, index) => (
                      <div
                        key={index}
                        className={cn(
                          "grid grid-cols-8 gap-2 p-2 text-sm border-t",
                          item.status === "fulfilled" && "bg-emerald-500/5",
                          item.status === "partial" && "bg-amber-500/5",
                          item.status === "shortage" && "bg-red-500/5",
                        )}
                      >
                        <div>{item.material_code}</div>
                        <div>{item.material_name}</div>
                        <div className="text-muted-foreground">
                          {item.specification || "-"}
                        </div>
                        <div>{item.required_qty}</div>
                        <div>{item.available_qty}</div>
                        <div>{item.in_transit_qty}</div>
                        <div
                          className={cn(
                            item.shortage_qty > 0 && "text-red-400 font-medium",
                          )}
                        >
                          {item.shortage_qty}
                        </div>
                        <div>
                          <Badge
                            variant="outline"
                            className={cn(
                              item.status === "fulfilled" &&
                                "bg-emerald-500 text-white",
                              item.status === "partial" &&
                                "bg-amber-500 text-white",
                              item.status === "shortage" &&
                                "bg-red-500 text-white",
                            )}
                          >
                            {item.status === "fulfilled"
                              ? "已齐套"
                              : item.status === "partial"
                                ? "部分"
                                : "缺料"}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                暂无数据
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDetailDialog(false)}
            >
              关闭
            </Button>
            {detailData && selectedWorkOrder && (
              <>
                <Button
                  variant="outline"
                  onClick={() => handleCheckKit(selectedWorkOrder.id)}
                  disabled={actionLoading}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  重新检查
                </Button>
                {detailData.kit_data?.kit_status === "complete" && (
                  <Button
                    onClick={() => handleConfirmStart(selectedWorkOrder.id)}
                    disabled={actionLoading}
                  >
                    <Play className="h-4 w-4 mr-2" />
                    确认开工
                  </Button>
                )}
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ===== MaterialAnalysis Tab Component (simplified without dangerouslySetInnerHTML) =====
function ProjectMaterialCard({ project }) {
  const [expanded, setExpanded] = useState(false);
  const stats = project.materialStats;
  const isAtRisk = project.readyRate < 80 || stats.delayed > 5;

  return (
    <motion.div
      layout
      className={cn(
        "rounded-xl border overflow-hidden transition-colors",
        isAtRisk
          ? "bg-red-500/5 border-red-500/30"
          : "bg-slate-800/50 border-slate-700/50",
      )}
    >
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs text-accent">
                {project.id}
              </span>
              {isAtRisk && (
                <Badge variant="destructive" className="text-[10px]">
                  <AlertTriangle className="w-3 h-3 mr-1" />
                  齐套风险
                </Badge>
              )}
            </div>
            <h3 className="font-semibold text-white">{project.name}</h3>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-white">
              {project.readyRate}%
            </div>
            <div className="text-xs text-slate-500">齐套率</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <Progress value={project.readyRate} className="h-2" />
        </div>

        {/* Material Stats Grid */}
        <div className="grid grid-cols-5 gap-2 mb-4">
          {[
            { key: "total", label: "总计", value: stats.total },
            { key: "arrived", label: "已到", value: stats.arrived },
            { key: "inTransit", label: "在途", value: stats.inTransit },
            { key: "delayed", label: "延期", value: stats.delayed },
            { key: "notOrdered", label: "未下单", value: stats.notOrdered },
          ].map((item) => (
            <div
              key={item.key}
              className={cn(
                "p-2 rounded-lg text-center",
                item.key === "delayed" && item.value > 0
                  ? "bg-red-500/10"
                  : item.key === "notOrdered" && item.value > 0
                    ? "bg-amber-500/10"
                    : "bg-slate-700/30",
              )}
            >
              <div
                className={cn(
                  "text-lg font-bold",
                  item.key === "delayed" && item.value > 0
                    ? "text-red-400"
                    : item.key === "notOrdered" && item.value > 0
                      ? "text-amber-400"
                      : "text-white",
                )}
              >
                {item.value}
              </div>
              <div className="text-[10px] text-slate-500">{item.label}</div>
            </div>
          ))}
        </div>

        {/* Assembly Date */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-400 flex items-center gap-1">
            <Calendar className="w-4 h-4" />
            计划装配：{project.planAssemblyDate}
          </span>
          <span
            className={cn(
              "font-medium",
              project.daysUntilAssembly <= 7
                ? "text-red-400"
                : project.daysUntilAssembly <= 14
                  ? "text-amber-400"
                  : "text-emerald-400",
            )}
          >
            剩余 {project.daysUntilAssembly} 天
          </span>
        </div>
      </div>

      {/* Critical Materials */}
      {project.criticalMaterials.length > 0 && (
        <div className="border-t border-border/50">
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full p-3 flex items-center justify-between text-sm hover:bg-slate-700/30 transition-colors"
          >
            <span className="text-slate-400 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              关键缺料 ({project.criticalMaterials.length})
            </span>
            <motion.span
              animate={{ rotate: expanded ? 180 : 0 }}
              className="text-slate-500"
            >
              ▼
            </motion.span>
          </button>

          <motion.div
            initial={false}
            animate={{ height: expanded ? "auto" : 0 }}
            className="overflow-hidden"
          >
            <div className="p-3 pt-0 space-y-2">
              {project.criticalMaterials.map((material, index) => (
                <div
                  key={index}
                  className="p-3 rounded-lg bg-slate-900/50 text-sm"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="font-mono text-xs text-slate-500 mb-0.5">
                        {material.code}
                      </div>
                      <div className="text-white">{material.name}</div>
                    </div>
                    <Badge
                      className={cn(
                        "border",
                        impactConfigs[material.impact].color,
                      )}
                    >
                      影响{impactConfigs[material.impact].label}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>数量：{material.qty}</span>
                    <span className={statusConfigs[material.status].textColor}>
                      {statusConfigs[material.status].label}
                    </span>
                    {material.expectedDate !== "-" && (
                      <span>预计：{material.expectedDate}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      )}
    </motion.div>
  );
}

function MaterialAnalysisTab() {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [projectMaterials, setProjectMaterials] = useState([]);
  const [trendPeriod, setTrendPeriod] = useState("week");
  const [trendData, setTrendData] = useState([]);
  const [loadingTrend, setLoadingTrend] = useState(false);

  const calculateMaterialStatus = (bomItems, purchaseItems) => {
    const stats = {
      total: bomItems.length,
      arrived: 0,
      inTransit: 0,
      delayed: 0,
      notOrdered: 0,
    };

    const criticalMaterials = [];

    bomItems.forEach((bomItem) => {
      const materialCode = bomItem.material_code;
      const relatedPurchaseItems = purchaseItems.filter(
        (item) => item.material_code === materialCode,
      );

      if (relatedPurchaseItems.length === 0) {
        stats.notOrdered++;
        criticalMaterials.push({
          code: materialCode,
          name: bomItem.material_name || "",
          qty: bomItem.quantity || 0,
          status: "not_ordered",
          expectedDate: "-",
          supplier: "-",
          impact: "high",
        });
      } else {
        const totalQty = relatedPurchaseItems.reduce(
          (sum, item) => sum + (item.quantity || 0),
          0,
        );
        const receivedQty = relatedPurchaseItems.reduce(
          (sum, item) => sum + (item.received_quantity || 0),
          0,
        );
        const requiredDate = bomItem.required_date || "";
        const now = new Date();
        const requiredDateObj = requiredDate ? new Date(requiredDate) : null;

        if (receivedQty >= totalQty) {
          stats.arrived++;
        } else if (receivedQty > 0) {
          stats.inTransit++;
          if (requiredDateObj && requiredDateObj < now) {
            stats.delayed++;
            criticalMaterials.push({
              code: materialCode,
              name: bomItem.material_name || "",
              qty: bomItem.quantity || 0,
              status: "delayed",
              expectedDate: relatedPurchaseItems[0].promised_date || "-",
              supplier: relatedPurchaseItems[0].supplier_name || "",
              impact: "high",
            });
          }
        } else {
          if (requiredDateObj && requiredDateObj < now) {
            stats.delayed++;
            criticalMaterials.push({
              code: materialCode,
              name: bomItem.material_name || "",
              qty: bomItem.quantity || 0,
              status: "delayed",
              expectedDate: relatedPurchaseItems[0].promised_date || "-",
              supplier: relatedPurchaseItems[0].supplier_name || "",
              impact: "high",
            });
          } else {
            stats.inTransit++;
          }
        }
      }
    });

    const readyRate =
      stats.total > 0 ? Math.round((stats.arrived / stats.total) * 100) : 100;

    return { stats, readyRate, criticalMaterials };
  };

  const loadProjectMaterials = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const projectsResponse = await projectApi.list({
        page: 1,
        page_size: 100,
        status: "ACTIVE",
      });
      const projects =
        projectsResponse.data?.items || projectsResponse.data || [];

      const projectMaterialsData = [];
      for (const project of projects) {
        try {
          const materialStatusResponse =
            await purchaseApi.kitRate.getProjectMaterialStatus(project.id);
          const materialStatus = materialStatusResponse.data || {};

          if (materialStatus.materials && materialStatus.materials.length > 0) {
            const materials = materialStatus.materials || [];

            const total = materials.length;
            const arrived = materials.filter(
              (m) => m.status === "fulfilled",
            ).length;
            const inTransit = materials.filter(
              (m) => m.total_in_transit_qty > 0,
            ).length;
            const delayed = materials.filter((m) => {
              return m.status === "shortage" || m.status === "partial";
            }).length;
            const notOrdered = materials.filter(
              (m) => m.status === "shortage" && m.total_available_qty === 0,
            ).length;

            const readyRate =
              total > 0 ? Math.round((arrived / total) * 100) : 100;

            const criticalMaterials = materials
              .filter(
                (m) =>
                  m.status === "shortage" ||
                  (m.status === "partial" && m.shortage_qty > 0),
              )
              .map((m) => ({
                code: m.material_code,
                name: m.material_name,
                qty: m.total_required_qty,
                status: m.status === "shortage" ? "not_ordered" : "delayed",
                expectedDate: "-",
                supplier: "-",
                impact: m.is_key_material ? "high" : "medium",
              }))
              .slice(0, 5);

            const planAssemblyDate = project.planned_end_date || "";
            const daysUntilAssembly = planAssemblyDate
              ? Math.max(
                  0,
                  Math.ceil(
                    (new Date(planAssemblyDate) - new Date()) /
                      (1000 * 60 * 60 * 24),
                  ),
                )
              : 0;

            projectMaterialsData.push({
              id: project.project_code || project.id?.toString(),
              name: project.project_name || "",
              planAssemblyDate: planAssemblyDate.split("T")[0] || "",
              daysUntilAssembly,
              materialStats: {
                total,
                arrived,
                inTransit,
                delayed,
                notOrdered,
              },
              readyRate,
              criticalMaterials,
            });
          }
        } catch (err) {
          console.error(
            `Failed to load material status for project ${project.id}:`,
            err,
          );
        }
      }

      setProjectMaterials(projectMaterialsData);
    } catch (err) {
      console.error("Failed to load project materials:", err);
      setError("加载物料数据失败");
      setProjectMaterials([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const filteredProjects = useMemo(() => {
    let filtered = projectMaterials;

    if (searchQuery) {
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          p.id.toLowerCase().includes(searchQuery.toLowerCase()),
      );
    }

    if (filterStatus === "at_risk") {
      filtered = filtered.filter(
        (p) => p.readyRate < 80 || p.materialStats.delayed > 5,
      );
    } else if (filterStatus === "upcoming") {
      filtered = filtered.filter(
        (p) => p.daysUntilAssembly <= 14 && p.daysUntilAssembly > 0,
      );
    }

    return filtered;
  }, [projectMaterials, searchQuery, filterStatus]);

  const overallStats = useMemo(() => {
    return filteredProjects.reduce(
      (acc, project) => {
        acc.total += project.materialStats.total;
        acc.arrived += project.materialStats.arrived;
        acc.delayed += project.materialStats.delayed;
        return acc;
      },
      { total: 0, arrived: 0, delayed: 0 },
    );
  }, [filteredProjects]);

  const overallReadyRate = useMemo(() => {
    return overallStats.total > 0
      ? Math.round((overallStats.arrived / overallStats.total) * 100)
      : 100;
  }, [overallStats]);

  const loadTrendData = useCallback(async () => {
    try {
      setLoadingTrend(true);
      const response = await purchaseApi.kitRate.trend({
        group_by: trendPeriod,
      });
      const trendResponse = response.data || {};
      const trendItems = trendResponse.trend_data || [];

      const formattedTrend = trendItems.map((item) => {
        const date = new Date(item.date);
        let label = "";

        if (trendPeriod === "day") {
          label = `${date.getMonth() + 1}/${date.getDate()}`;
        } else if (trendPeriod === "week") {
          const weekNum = Math.ceil(date.getDate() / 7);
          label = `第${weekNum}周`;
        } else {
          label = `${date.getMonth() + 1}月`;
        }

        return {
          label,
          value: Math.round(item.kit_rate || 0),
        };
      });

      setTrendData(formattedTrend);
    } catch (err) {
      console.error("Failed to load trend data:", err);
      const days = trendPeriod === "day" ? 7 : trendPeriod === "week" ? 4 : 6;
      const baseRate = overallReadyRate;

      const mockTrend = Array.from({ length: days }, (_, i) => {
        const variation = (Math.random() - 0.5) * 10;
        const rate = Math.max(0, Math.min(100, baseRate + variation));
        const label =
          trendPeriod === "day"
            ? `${days - i}天前`
            : trendPeriod === "week"
              ? `第${days - i}周`
              : `${new Date().getMonth() - (days - i - 1)}月`;

        return { label, value: Math.round(rate) };
      }).reverse();

      setTrendData(mockTrend);
    } finally {
      setLoadingTrend(false);
    }
  }, [trendPeriod, overallReadyRate]);

  useEffect(() => {
    loadProjectMaterials();
  }, [loadProjectMaterials]);

  useEffect(() => {
    if (!loading && projectMaterials.length > 0) {
      loadTrendData();
    }
  }, [trendPeriod, loading, projectMaterials.length, loadTrendData]);

  const kitRateDistribution = useMemo(() => {
    const distribution = {
      perfect: 0,
      good: 0,
      warning: 0,
      danger: 0,
    };

    filteredProjects.forEach((project) => {
      if (project.readyRate >= 100) {
        distribution.perfect++;
      } else if (project.readyRate >= 80) {
        distribution.good++;
      } else if (project.readyRate >= 60) {
        distribution.warning++;
      } else {
        distribution.danger++;
      }
    });

    return [
      { label: "100%", value: distribution.perfect, color: "#10b981" },
      { label: "80-99%", value: distribution.good, color: "#3b82f6" },
      { label: "60-79%", value: distribution.warning, color: "#f59e0b" },
      { label: "<60%", value: distribution.danger, color: "#ef4444" },
    ];
  }, [filteredProjects]);

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
      >
        {[
          {
            label: "整体齐套率",
            value: `${overallReadyRate}%`,
            icon: Package,
            color:
              overallReadyRate >= 80
                ? "text-emerald-400"
                : "text-amber-400",
          },
          {
            label: "延期物料",
            value: overallStats.delayed,
            icon: AlertTriangle,
            color: "text-red-400",
          },
          {
            label: "在途物料",
            value: filteredProjects.reduce(
              (sum, p) => sum + p.materialStats.inTransit,
              0,
            ),
            icon: Truck,
            color: "text-blue-400",
          },
          {
            label: "风险项目",
            value: filteredProjects.filter((p) => p.readyRate < 80).length,
            icon: Box,
            color: "text-amber-400",
          },
        ].map((stat, index) => (
          <Card key={index} className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">{stat.label}</p>
                  <p className="text-2xl font-bold text-white mt-1">
                    {stat.value}
                  </p>
                </div>
                <stat.icon className={cn("w-8 h-8", stat.color)} />
              </div>
            </CardContent>
          </Card>
        ))}
      </motion.div>

      {/* Filters */}
      <motion.div variants={fadeIn}>
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardContent className="p-4">
            <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
              <div className="flex items-center gap-2 flex-wrap">
                {[
                  { value: "all", label: "全部项目" },
                  { value: "at_risk", label: "风险项目" },
                  { value: "upcoming", label: "即将装配" },
                ].map((filter) => (
                  <Button
                    key={filter.value}
                    variant={
                      filterStatus === filter.value ? "default" : "ghost"
                    }
                    size="sm"
                    onClick={() => setFilterStatus(filter.value)}
                  >
                    {filter.label}
                  </Button>
                ))}
              </div>
              <div className="flex items-center gap-2 w-full md:w-auto">
                <div className="relative flex-1 md:w-64">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    placeholder="搜索项目..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Loading State */}
      {loading && (
        <motion.div variants={fadeIn} className="text-center py-16">
          <div className="inline-block">
            <RefreshCw className="w-8 h-8 animate-spin text-slate-400 mb-4" />
            <div className="text-slate-400">加载项目物料数据中...</div>
          </div>
        </motion.div>
      )}

      {/* Error State */}
      {error && !loading && (
        <motion.div
          variants={fadeIn}
          className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm"
        >
          {error}
        </motion.div>
      )}

      {/* Project Material Cards */}
      {!loading && !error && (
        <>
          {filteredProjects.length > 0 ? (
            <motion.div
              variants={fadeIn}
              className="grid grid-cols-1 lg:grid-cols-2 gap-6"
            >
              {filteredProjects.map((project) => (
                <ProjectMaterialCard key={project.id} project={project} />
              ))}
            </motion.div>
          ) : (
            <motion.div variants={fadeIn}>
              <Card className="bg-slate-800/50 border-slate-700/50">
                <CardContent className="py-16 text-center">
                  <Package className="w-16 h-16 mx-auto mb-4 text-slate-500" />
                  <h3 className="text-lg font-semibold text-white mb-2">
                    暂无项目数据
                  </h3>
                  <p className="text-sm text-slate-400 mb-4">
                    {searchQuery || filterStatus !== "all"
                      ? "没有找到匹配的项目，请尝试调整筛选条件"
                      : "当前没有活跃项目或项目物料数据"}
                  </p>
                  {(searchQuery || filterStatus !== "all") && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSearchQuery("");
                        setFilterStatus("all");
                      }}
                    >
                      清除筛选条件
                    </Button>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )}
        </>
      )}
    </div>
  );
}

// ===== Main Component =====
export default function MaterialReadiness() {
  const [activeTab, setActiveTab] = useState("check");

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="齐套管理"
        description="统一管理物料齐套检查和分析"
      />

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="check" className="gap-2">
            <CheckCircle2 className="w-4 h-4" />
            齐套检查
          </TabsTrigger>
          <TabsTrigger value="analysis" className="gap-2">
            <Package className="w-4 h-4" />
            齐套分析
          </TabsTrigger>
        </TabsList>

        <TabsContent value="check" className="mt-6">
          <KitCheckTab />
        </TabsContent>

        <TabsContent value="analysis" className="mt-6">
          <MaterialAnalysisTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
