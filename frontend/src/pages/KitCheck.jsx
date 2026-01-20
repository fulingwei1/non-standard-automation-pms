/**
 * Kit Check - 齐套检查
 * 工单物料齐套检查与开工前确认
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
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
  TrendingUp } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Input,
  Badge,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../components/ui";
import { cn, formatDate } from "../lib/utils";
import { fadeIn } from "../lib/animations";
import { kitCheckApi } from "../services/api";

const kitStatusConfigs = {
  complete: {
    label: "完全齐套",
    color: "bg-emerald-500",
    textColor: "text-emerald-400"
  },
  partial: {
    label: "部分齐套",
    color: "bg-amber-500",
    textColor: "text-amber-400"
  },
  shortage: { label: "缺料", color: "bg-red-500", textColor: "text-red-400" }
};

export default function KitCheck() {
  const _navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [workOrders, setWorkOrders] = useState([]);
  const [summary, setSummary] = useState({
    total: 0,
    complete: 0,
    partial: 0,
    shortage: 0
  });
  const [filters, setFilters] = useState({
    kit_status: "all",
    workshop_id: "",
    project_id: "",
    plan_date: "",
    keyword: ""
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
        page_size: pageSize
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
      const res = await kitCheckApi.workOrders.list(params);
      if (res.data.code === 200) {
        setWorkOrders(res.data.data.work_orders || []);
        setSummary(res.data.data.summary || {});
        setTotal(res.data.data.pagination?.total || 0);
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
      const res = await kitCheckApi.workOrders.get(workOrderId);
      if (res.data.code === 200) {
        setDetailData(res.data.data);
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
      await kitCheckApi.workOrders.check(workOrderId);
      alert("齐套检查完成");
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
    if (!confirm(`确认工单物料齐套，可以开工吗？`)) {return;}

    setActionLoading(true);
    try {
      await kitCheckApi.workOrders.confirm(workOrderId, {
        confirm_type: confirmType,
        confirm_note: "确认开工"
      });
      alert("开工确认成功");
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
    <div className="space-y-6 p-6">
      <PageHeader title="齐套检查" description="工单物料齐套检查与开工前确认" />

      {/* 统计卡片 */}
      <motion.div
        variants={fadeIn}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 md:grid-cols-4 gap-4">

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
                }>

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
                onChange={(e) => handleFilterChange("keyword", e.target.value)} />

            </div>

            <div>
              <Input
                type="date"
                placeholder="计划开工日期"
                value={filters.plan_date}
                onChange={(e) =>
                handleFilterChange("plan_date", e.target.value)
                } />

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
          {loading ?
          <div className="text-center py-8 text-muted-foreground">
              加载中...
          </div> :
          workOrders.length === 0 ?
          <div className="text-center py-8 text-muted-foreground">
              暂无待检查工单
          </div> :

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
                    wo.kit_status === "shortage" && "bg-red-500/5"
                  )}>

                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-medium">{wo.work_order_no}</span>
                        <Badge
                        variant="outline"
                        className={cn(status.color, "text-white")}>

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
                        {wo.plan_start_date ?
                      formatDate(wo.plan_start_date) :
                      "-"}
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
                              wo.kit_status === "shortage" && "bg-red-500"
                            )}
                            style={{ width: `${wo.kit_rate}%` }} />

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
                      onClick={() => handleViewDetail(wo)}>

                        <Eye className="h-4 w-4 mr-2" />
                        查看详情
                      </Button>
                      <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleCheckKit(wo.id)}
                      disabled={actionLoading}>

                        <RefreshCw className="h-4 w-4 mr-2" />
                        检查
                      </Button>
                    </div>
                </div>);

            })}
          </div>
          }

          {total > pageSize &&
          <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <div className="text-sm text-muted-foreground">
                共 {total} 条记录，第 {page} / {Math.ceil(total / pageSize)} 页
              </div>
              <div className="flex items-center gap-2">
                <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1 || loading}>

                  上一页
                </Button>
                <Button
                variant="outline"
                size="sm"
                onClick={() =>
                setPage((p) => Math.min(Math.ceil(total / pageSize), p + 1))
                }
                disabled={page >= Math.ceil(total / pageSize) || loading}>

                  下一页
                </Button>
              </div>
          </div>
          }
        </CardContent>
      </Card>

      {/* 详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>工单齐套详情</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {detailLoading ?
            <div className="text-center py-8 text-muted-foreground">
                加载中...
            </div> :
            detailData ?
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
                      {detailData.work_order?.plan_start_date ?
                    formatDate(detailData.work_order.plan_start_date) :
                    "-"}
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
                    {detailData.bom_items?.map((item, index) =>
                  <div
                    key={index}
                    className={cn(
                      "grid grid-cols-8 gap-2 p-2 text-sm border-t",
                      item.status === "fulfilled" && "bg-emerald-500/5",
                      item.status === "partial" && "bg-amber-500/5",
                      item.status === "shortage" && "bg-red-500/5"
                    )}>

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
                        item.shortage_qty > 0 && "text-red-400 font-medium"
                      )}>

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
                          "bg-red-500 text-white"
                        )}>

                            {item.status === "fulfilled" ?
                        "已齐套" :
                        item.status === "partial" ?
                        "部分" :
                        "缺料"}
                          </Badge>
                        </div>
                  </div>
                  )}
                  </div>
                </div>
            </div> :

            <div className="text-center py-8 text-muted-foreground">
                暂无数据
            </div>
            }
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDetailDialog(false)}>

              关闭
            </Button>
            {detailData && selectedWorkOrder &&
            <>
                <Button
                variant="outline"
                onClick={() => handleCheckKit(selectedWorkOrder.id)}
                disabled={actionLoading}>

                  <RefreshCw className="h-4 w-4 mr-2" />
                  重新检查
                </Button>
                {detailData.kit_data?.kit_status === "complete" &&
              <Button
                onClick={() => handleConfirmStart(selectedWorkOrder.id)}
                disabled={actionLoading}>

                    <Play className="h-4 w-4 mr-2" />
                    确认开工
              </Button>
              }
            </>
            }
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}