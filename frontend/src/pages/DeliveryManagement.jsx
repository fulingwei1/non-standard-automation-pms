/**
 * Delivery Management - PMC发货管理页面
 * Features: 发货计划、发货订单列表、待发货数、在途订单数
 * 由PMC负责填写和管理
 */

import { useState, useEffect, useCallback, useMemo } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Truck,
  Calendar,
  Package,
  MapPin,
  Clock,
  CheckCircle2,
  AlertCircle,
  Search,
  Filter,
  Plus,
  Edit,
  Eye,
  FileText,
  TrendingUp,
  PackageCheck,
  PackageX,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody,
  Label,
  Textarea,
} from "../components/ui";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { cn } from "../lib/utils";
import { businessSupportApi } from "../services/api";

// 发货状态映射
const deliveryStatusMap = {
  draft: { label: "草稿", color: "bg-slate-500/20 text-slate-400" },
  approved: { label: "已审批", color: "bg-blue-500/20 text-blue-400" },
  printed: { label: "已打印", color: "bg-purple-500/20 text-purple-400" },
  shipped: { label: "已发货", color: "bg-amber-500/20 text-amber-400" },
  received: { label: "已签收", color: "bg-emerald-500/20 text-emerald-400" },
  returned: { label: "已退回", color: "bg-red-500/20 text-red-400" },
};

// 审批状态映射
const approvalStatusMap = {
  pending: { label: "待审批", color: "bg-slate-500/20 text-slate-400" },
  approved: { label: "已审批", color: "bg-emerald-500/20 text-emerald-400" },
  rejected: { label: "已拒绝", color: "bg-red-500/20 text-red-400" },
};

export default function DeliveryManagement() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("orders");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 筛选条件
  const [searchKeyword, setSearchKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState(
    searchParams.get("status") || "all",
  );
  const [approvalFilter, setApprovalFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  // 数据
  const [deliveryOrders, setDeliveryOrders] = useState([]);
  const [total, setTotal] = useState(0);
  const [statistics, setStatistics] = useState({
    pendingShipments: 0,
    shippedToday: 0,
    inTransit: 0,
    deliveredThisWeek: 0,
    onTimeShippingRate: 0,
    avgShippingTime: 0,
    totalOrders: 0,
  });

  // 创建发货单对话框
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // 加载统计数据
  const loadStatistics = useCallback(async () => {
    try {
      const response = await businessSupportApi.deliveryOrders.statistics();
      const data = response?.data?.data || response?.data;
      if (data) {
        setStatistics({
          pendingShipments: data.pending_shipments || 0,
          shippedToday: data.shipped_today || 0,
          inTransit: data.in_transit || 0,
          deliveredThisWeek: data.delivered_this_week || 0,
          onTimeShippingRate: data.on_time_shipping_rate || 0,
          avgShippingTime: data.avg_shipping_time || 0,
          totalOrders: data.total_orders || 0,
        });
      }
    } catch (err) {
      console.error("Failed to load delivery statistics:", err);
    }
  }, []);

  // 加载发货订单列表
  const loadDeliveryOrders = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page,
        page_size: pageSize,
      };

      if (searchKeyword) {
        params.search = searchKeyword;
      }

      if (statusFilter !== "all") {
        params.delivery_status = statusFilter;
      }

      if (approvalFilter !== "all") {
        params.approval_status = approvalFilter;
      }

      const response = await businessSupportApi.deliveryOrders.list(params);
      const data = response?.data?.data || response?.data;
      const items = data?.items || data?.data?.items || [];
      const totalCount = data?.total || data?.data?.total || 0;

      setDeliveryOrders(Array.isArray(items) ? items : []);
      setTotal(totalCount);
    } catch (err) {
      console.error("Failed to load delivery orders:", err);
      setError("加载发货订单失败");
      setDeliveryOrders([]);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, searchKeyword, statusFilter, approvalFilter]);

  useEffect(() => {
    loadStatistics();
  }, [loadStatistics]);

  useEffect(() => {
    loadDeliveryOrders();
  }, [loadDeliveryOrders]);

  // 根据URL参数设置Tab和筛选
  useEffect(() => {
    const status = searchParams.get("status");
    if (status === "pending") {
      setActiveTab("pending");
      setStatusFilter("approved");
      setApprovalFilter("approved");
    } else if (status === "in_transit") {
      setActiveTab("in_transit");
      setStatusFilter("shipped");
    } else {
      setActiveTab("orders");
    }
  }, [searchParams]);

  // Tab切换时更新筛选条件
  useEffect(() => {
    if (activeTab === "pending") {
      setStatusFilter("approved");
      setApprovalFilter("approved");
    } else if (activeTab === "in_transit") {
      setStatusFilter("shipped");
    } else if (activeTab === "orders") {
      // 重置筛选
      if (!searchParams.get("status")) {
        setStatusFilter("all");
        setApprovalFilter("all");
      }
    }
  }, [activeTab, searchParams]);

  // 格式化日期
  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleDateString("zh-CN");
  };

  // 格式化日期时间
  const formatDateTime = (dateStr) => {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleString("zh-CN");
  };

  // 过滤后的订单
  const filteredOrders = useMemo(() => {
    return deliveryOrders;
  }, [deliveryOrders]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <PageHeader
        title="发货管理"
        description="发货计划、订单管理、状态跟踪"
        icon={Truck}
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="bg-surface-50 border-white/10">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">待发货</p>
                  <p className="text-2xl font-bold text-white">
                    {statistics.pendingShipments}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-lg bg-amber-500/10 flex items-center justify-center">
                  <Package className="w-6 h-6 text-amber-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-surface-50 border-white/10">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">今日已发</p>
                  <p className="text-2xl font-bold text-white">
                    {statistics.shippedToday}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                  <PackageCheck className="w-6 h-6 text-emerald-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-surface-50 border-white/10">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">在途订单</p>
                  <p className="text-2xl font-bold text-white">
                    {statistics.inTransit}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center">
                  <Truck className="w-6 h-6 text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-surface-50 border-white/10">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">准时发货率</p>
                  <p className="text-2xl font-bold text-white">
                    {statistics.onTimeShippingRate.toFixed(1)}%
                  </p>
                </div>
                <div className="w-12 h-12 rounded-lg bg-purple-500/10 flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-purple-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 主要内容 */}
        <Card className="bg-surface-50 border-white/10">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Truck className="w-5 h-5 text-primary" />
                发货订单管理
              </CardTitle>
              <Button
                onClick={() => setCreateDialogOpen(true)}
                className="bg-primary hover:bg-primary/90"
              >
                <Plus className="w-4 h-4 mr-2" />
                创建发货单
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs
              value={activeTab}
              onValueChange={setActiveTab}
              className="space-y-4"
            >
              <TabsList className="bg-surface-100 border-white/10">
                <TabsTrigger value="orders">全部订单</TabsTrigger>
                <TabsTrigger value="pending">待发货</TabsTrigger>
                <TabsTrigger value="in_transit">在途订单</TabsTrigger>
                <TabsTrigger value="plan">发货计划</TabsTrigger>
              </TabsList>

              {/* 筛选栏 */}
              <div className="flex items-center gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    placeholder="搜索订单号、客户名称、项目名称..."
                    value={searchKeyword}
                    onChange={(e) => setSearchKeyword(e.target.value)}
                    className="pl-10 bg-surface-100 border-white/10"
                  />
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-40 bg-surface-100 border-white/10">
                    <SelectValue placeholder="全部状态" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">全部状态</SelectItem>
                    <SelectItem value="draft">草稿</SelectItem>
                    <SelectItem value="approved">已审批</SelectItem>
                    <SelectItem value="printed">已打印</SelectItem>
                    <SelectItem value="shipped">已发货</SelectItem>
                    <SelectItem value="received">已签收</SelectItem>
                  </SelectContent>
                </Select>
                <Select
                  value={approvalFilter}
                  onValueChange={setApprovalFilter}
                >
                  <SelectTrigger className="w-40 bg-surface-100 border-white/10">
                    <SelectValue placeholder="全部审批" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">全部审批</SelectItem>
                    <SelectItem value="pending">待审批</SelectItem>
                    <SelectItem value="approved">已审批</SelectItem>
                    <SelectItem value="rejected">已拒绝</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* 全部订单 */}
              <TabsContent value="orders" className="space-y-4">
                {loading && (
                  <div className="text-center py-8 text-slate-400">
                    加载中...
                  </div>
                )}
                {error && (
                  <div className="text-center py-8 text-red-400">{error}</div>
                )}
                {!loading && !error && filteredOrders.length === 0 && (
                  <div className="text-center py-8 text-slate-400">
                    暂无发货订单
                  </div>
                )}
                {!loading && !error && filteredOrders.length > 0 && (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-white/10">
                          <TableHead className="text-slate-300">
                            发货单号
                          </TableHead>
                          <TableHead className="text-slate-300">
                            项目订单
                          </TableHead>
                          <TableHead className="text-slate-300">客户</TableHead>
                          <TableHead className="text-slate-300">
                            目的地
                          </TableHead>
                          <TableHead className="text-slate-300">
                            发货日期
                          </TableHead>
                          <TableHead className="text-slate-300">
                            订单状态
                          </TableHead>
                          <TableHead className="text-slate-300">
                            审批状态
                          </TableHead>
                          <TableHead className="text-slate-300">操作</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredOrders.map((order) => (
                          <TableRow
                            key={order.id}
                            className="border-white/10 hover:bg-white/5"
                          >
                            <TableCell className="font-medium text-white">
                              {order.delivery_no}
                            </TableCell>
                            <TableCell>
                              <div>
                                <p className="text-white">
                                  {order.order_no || "-"}
                                </p>
                                {order.project_id && (
                                  <p className="text-xs text-slate-400">
                                    项目ID: {order.project_id}
                                  </p>
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              <div>
                                <p className="text-white">
                                  {order.customer_name || "-"}
                                </p>
                                {order.receiver_name && (
                                  <p className="text-xs text-slate-400">
                                    收货人: {order.receiver_name}
                                  </p>
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-1 text-slate-300">
                                <MapPin className="w-4 h-4" />
                                <span>{order.receiver_address || "-"}</span>
                              </div>
                            </TableCell>
                            <TableCell className="text-slate-300">
                              {formatDate(order.delivery_date)}
                            </TableCell>
                            <TableCell>
                              <Badge
                                className={cn(
                                  "text-xs",
                                  deliveryStatusMap[order.delivery_status]
                                    ?.color || "bg-slate-500/20 text-slate-400",
                                )}
                              >
                                {deliveryStatusMap[order.delivery_status]
                                  ?.label || order.delivery_status}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge
                                className={cn(
                                  "text-xs",
                                  approvalStatusMap[order.approval_status]
                                    ?.color || "bg-slate-500/20 text-slate-400",
                                )}
                              >
                                {approvalStatusMap[order.approval_status]
                                  ?.label || order.approval_status}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() =>
                                    navigate(`/pmc/delivery-orders/${order.id}`)
                                  }
                                >
                                  <Eye className="w-4 h-4" />
                                </Button>
                                {order.delivery_status === "draft" && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() =>
                                      navigate(
                                        `/pmc/delivery-orders/${order.id}/edit`,
                                      )
                                    }
                                  >
                                    <Edit className="w-4 h-4" />
                                  </Button>
                                )}
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}

                {/* 分页 */}
                {total > pageSize && (
                  <div className="flex items-center justify-between pt-4">
                    <p className="text-sm text-slate-400">
                      共 {total} 条记录，第 {page} /{" "}
                      {Math.ceil(total / pageSize)} 页
                    </p>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1}
                      >
                        上一页
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          setPage((p) =>
                            Math.min(Math.ceil(total / pageSize), p + 1),
                          )
                        }
                        disabled={page >= Math.ceil(total / pageSize)}
                      >
                        下一页
                      </Button>
                    </div>
                  </div>
                )}
              </TabsContent>

              {/* 待发货 */}
              <TabsContent value="pending" className="space-y-4">
                {loading && (
                  <div className="text-center py-8 text-slate-400">
                    加载中...
                  </div>
                )}
                {error && (
                  <div className="text-center py-8 text-red-400">{error}</div>
                )}
                {!loading && !error && filteredOrders.length === 0 && (
                  <div className="text-center py-8 text-slate-400">
                    待发货订单：{statistics.pendingShipments} 单
                  </div>
                )}
                {!loading && !error && filteredOrders.length > 0 && (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-white/10">
                          <TableHead className="text-slate-300">
                            发货单号
                          </TableHead>
                          <TableHead className="text-slate-300">
                            项目订单
                          </TableHead>
                          <TableHead className="text-slate-300">客户</TableHead>
                          <TableHead className="text-slate-300">
                            目的地
                          </TableHead>
                          <TableHead className="text-slate-300">
                            计划发货日期
                          </TableHead>
                          <TableHead className="text-slate-300">操作</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredOrders
                          .filter(
                            (order) => order.delivery_status === "approved",
                          )
                          .map((order) => (
                            <TableRow
                              key={order.id}
                              className="border-white/10 hover:bg-white/5"
                            >
                              <TableCell className="font-medium text-white">
                                {order.delivery_no}
                              </TableCell>
                              <TableCell>
                                <div>
                                  <p className="text-white">
                                    {order.order_no || "-"}
                                  </p>
                                  {order.project_id && (
                                    <p className="text-xs text-slate-400">
                                      项目ID: {order.project_id}
                                    </p>
                                  )}
                                </div>
                              </TableCell>
                              <TableCell>
                                <div>
                                  <p className="text-white">
                                    {order.customer_name || "-"}
                                  </p>
                                  {order.receiver_name && (
                                    <p className="text-xs text-slate-400">
                                      收货人: {order.receiver_name}
                                    </p>
                                  )}
                                </div>
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-1 text-slate-300">
                                  <MapPin className="w-4 h-4" />
                                  <span>{order.receiver_address || "-"}</span>
                                </div>
                              </TableCell>
                              <TableCell className="text-slate-300">
                                {formatDate(order.delivery_date)}
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-2">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() =>
                                      navigate(
                                        `/pmc/delivery-orders/${order.id}`,
                                      )
                                    }
                                  >
                                    <Eye className="w-4 h-4" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() =>
                                      navigate(
                                        `/pmc/delivery-orders/${order.id}/edit`,
                                      )
                                    }
                                  >
                                    <Edit className="w-4 h-4" />
                                  </Button>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </TabsContent>

              {/* 在途订单 */}
              <TabsContent value="in_transit" className="space-y-4">
                {loading && (
                  <div className="text-center py-8 text-slate-400">
                    加载中...
                  </div>
                )}
                {error && (
                  <div className="text-center py-8 text-red-400">{error}</div>
                )}
                {!loading && !error && filteredOrders.length === 0 && (
                  <div className="text-center py-8 text-slate-400">
                    在途订单：{statistics.inTransit} 单
                  </div>
                )}
                {!loading && !error && filteredOrders.length > 0 && (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-white/10">
                          <TableHead className="text-slate-300">
                            发货单号
                          </TableHead>
                          <TableHead className="text-slate-300">
                            项目订单
                          </TableHead>
                          <TableHead className="text-slate-300">客户</TableHead>
                          <TableHead className="text-slate-300">
                            目的地
                          </TableHead>
                          <TableHead className="text-slate-300">
                            发货日期
                          </TableHead>
                          <TableHead className="text-slate-300">
                            物流单号
                          </TableHead>
                          <TableHead className="text-slate-300">
                            预计到达
                          </TableHead>
                          <TableHead className="text-slate-300">操作</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredOrders
                          .filter(
                            (order) =>
                              order.delivery_status === "shipped" &&
                              !order.receive_date,
                          )
                          .map((order) => (
                            <TableRow
                              key={order.id}
                              className="border-white/10 hover:bg-white/5"
                            >
                              <TableCell className="font-medium text-white">
                                {order.delivery_no}
                              </TableCell>
                              <TableCell>
                                <div>
                                  <p className="text-white">
                                    {order.order_no || "-"}
                                  </p>
                                  {order.project_id && (
                                    <p className="text-xs text-slate-400">
                                      项目ID: {order.project_id}
                                    </p>
                                  )}
                                </div>
                              </TableCell>
                              <TableCell>
                                <div>
                                  <p className="text-white">
                                    {order.customer_name || "-"}
                                  </p>
                                  {order.receiver_name && (
                                    <p className="text-xs text-slate-400">
                                      收货人: {order.receiver_name}
                                    </p>
                                  )}
                                </div>
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-1 text-slate-300">
                                  <MapPin className="w-4 h-4" />
                                  <span>{order.receiver_address || "-"}</span>
                                </div>
                              </TableCell>
                              <TableCell className="text-slate-300">
                                {formatDateTime(order.ship_date)}
                              </TableCell>
                              <TableCell className="text-slate-300">
                                {order.tracking_no || "-"}
                              </TableCell>
                              <TableCell className="text-slate-300">
                                {order.delivery_date ? (
                                  <div className="flex items-center gap-1">
                                    <Calendar className="w-4 h-4" />
                                    {formatDate(order.delivery_date)}
                                  </div>
                                ) : (
                                  "-"
                                )}
                              </TableCell>
                              <TableCell>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() =>
                                    navigate(`/pmc/delivery-orders/${order.id}`)
                                  }
                                >
                                  <Eye className="w-4 h-4" />
                                </Button>
                              </TableCell>
                            </TableRow>
                          ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </TabsContent>

              {/* 发货计划 */}
              <TabsContent value="plan" className="space-y-4">
                <Card className="bg-surface-100 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-base">发货计划</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center py-8 text-slate-400">
                      发货计划功能开发中...
                      <br />
                      <span className="text-xs">
                        将支持创建、编辑、查看发货计划
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>

      {/* 创建发货单对话框 */}
      <CreateDeliveryOrderDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSuccess={() => {
          setCreateDialogOpen(false);
          loadDeliveryOrders();
          loadStatistics();
        }}
      />
    </div>
  );
}

// 创建发货单对话框组件
function CreateDeliveryOrderDialog({ open, onOpenChange, onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [salesOrders, setSalesOrders] = useState([]);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [formData, setFormData] = useState({
    order_id: "",
    delivery_date: new Date().toISOString().split("T")[0],
    delivery_type: "logistics",
    logistics_company: "",
    tracking_no: "",
    receiver_name: "",
    receiver_phone: "",
    receiver_address: "",
    delivery_amount: "",
    special_approval: false,
    special_approval_reason: "",
    remark: "",
  });
  const [selectedSalesOrder, setSelectedSalesOrder] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // 加载销售订单列表
  const loadSalesOrders = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        page: 1,
        page_size: 50,
      };
      if (searchKeyword) {
        params.search = searchKeyword;
      }
      // 只显示已确认的订单
      params.order_status = "confirmed";

      const response = await businessSupportApi.salesOrders.list(params);
      const data = response?.data?.data || response?.data;
      const items = data?.items || data?.data?.items || [];
      setSalesOrders(Array.isArray(items) ? items : []);
    } catch (err) {
      console.error("Failed to load sales orders:", err);
      setSalesOrders([]);
    } finally {
      setLoading(false);
    }
  }, [searchKeyword]);

  useEffect(() => {
    if (open) {
      loadSalesOrders();
      // 重置表单
      setFormData({
        order_id: "",
        delivery_date: new Date().toISOString().split("T")[0],
        delivery_type: "logistics",
        logistics_company: "",
        tracking_no: "",
        receiver_name: "",
        receiver_phone: "",
        receiver_address: "",
        delivery_amount: "",
        special_approval: false,
        special_approval_reason: "",
        remark: "",
      });
      setSelectedSalesOrder(null);
      setError(null);
    }
  }, [open, loadSalesOrders]);

  // 选择销售订单
  const handleSelectOrder = (order) => {
    setSelectedSalesOrder(order);
    setFormData((prev) => ({
      ...prev,
      order_id: order.id,
      receiver_name: order.customer_name || "",
      receiver_address: order.delivery_address || "",
      delivery_amount: order.total_amount || "",
    }));
  };

  // 提交表单
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // 验证必填字段
    if (!formData.order_id) {
      setError("请选择销售订单");
      return;
    }
    if (!formData.delivery_date) {
      setError("请选择发货日期");
      return;
    }
    if (!formData.delivery_type) {
      setError("请选择发货方式");
      return;
    }
    if (
      !formData.delivery_amount ||
      parseFloat(formData.delivery_amount) <= 0
    ) {
      setError("请输入有效的发货金额");
      return;
    }

    try {
      setSubmitting(true);
      const submitData = {
        order_id: parseInt(formData.order_id),
        delivery_date: formData.delivery_date,
        delivery_type: formData.delivery_type,
        logistics_company: formData.logistics_company || null,
        tracking_no: formData.tracking_no || null,
        receiver_name: formData.receiver_name || null,
        receiver_phone: formData.receiver_phone || null,
        receiver_address: formData.receiver_address || null,
        delivery_amount: parseFloat(formData.delivery_amount),
        special_approval: formData.special_approval,
        special_approval_reason: formData.special_approval_reason || null,
        remark: formData.remark || null,
      };

      const response =
        await businessSupportApi.deliveryOrders.create(submitData);
      if (response?.data?.code === 200 || response?.status === 200) {
        onSuccess();
      } else {
        setError(response?.data?.message || "创建发货单失败");
      }
    } catch (err) {
      console.error("Failed to create delivery order:", err);
      setError(err?.response?.data?.detail || err?.message || "创建发货单失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>创建发货单</DialogTitle>
        </DialogHeader>

        <DialogBody>
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="p-3 rounded-lg bg-red-500/10 text-red-400 text-sm">
                {error}
              </div>
            )}

            {/* 选择销售订单 */}
            <div className="space-y-2">
              <Label>销售订单 *</Label>
              <div className="space-y-2">
                <Input
                  placeholder="搜索订单号、客户名称..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      loadSalesOrders();
                    }
                  }}
                  className="bg-surface-100 border-white/10"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={loadSalesOrders}
                  disabled={loading}
                >
                  <Search className="w-4 h-4 mr-2" />
                  搜索
                </Button>
              </div>
              {loading ? (
                <div className="text-center py-4 text-slate-400">加载中...</div>
              ) : salesOrders.length === 0 ? (
                <div className="text-center py-4 text-slate-400">
                  暂无销售订单
                </div>
              ) : (
                <div className="max-h-48 overflow-y-auto border border-white/10 rounded-lg">
                  {salesOrders.map((order) => (
                    <div
                      key={order.id}
                      onClick={() => handleSelectOrder(order)}
                      className={cn(
                        "p-3 cursor-pointer border-b border-white/10 hover:bg-white/5 transition-colors",
                        selectedSalesOrder?.id === order.id &&
                          "bg-primary/20 border-primary/50",
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-white font-medium">
                            {order.order_no}
                          </p>
                          <p className="text-sm text-slate-400">
                            {order.customer_name} | 项目:{" "}
                            {order.project_id || "-"}
                          </p>
                          <p className="text-xs text-slate-500">
                            订单金额: ¥
                            {order.total_amount?.toLocaleString() || "0"}
                          </p>
                        </div>
                        {selectedSalesOrder?.id === order.id && (
                          <CheckCircle2 className="w-5 h-5 text-primary" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 发货信息 */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>发货日期 *</Label>
                <Input
                  type="date"
                  value={formData.delivery_date}
                  onChange={(e) =>
                    setFormData({ ...formData, delivery_date: e.target.value })
                  }
                  className="bg-surface-100 border-white/10"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>发货方式 *</Label>
                <Select
                  value={formData.delivery_type}
                  onValueChange={(value) =>
                    setFormData({ ...formData, delivery_type: value })
                  }
                >
                  <SelectTrigger className="bg-surface-100 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="express">快递</SelectItem>
                    <SelectItem value="logistics">物流</SelectItem>
                    <SelectItem value="self_pickup">自提</SelectItem>
                    <SelectItem value="install">安装</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* 物流信息 */}
            {formData.delivery_type === "express" ||
            formData.delivery_type === "logistics" ? (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>物流公司</Label>
                  <Input
                    value={formData.logistics_company}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        logistics_company: e.target.value,
                      })
                    }
                    placeholder="请输入物流公司"
                    className="bg-surface-100 border-white/10"
                  />
                </div>
                <div className="space-y-2">
                  <Label>物流单号</Label>
                  <Input
                    value={formData.tracking_no}
                    onChange={(e) =>
                      setFormData({ ...formData, tracking_no: e.target.value })
                    }
                    placeholder="请输入物流单号"
                    className="bg-surface-100 border-white/10"
                  />
                </div>
              </div>
            ) : null}

            {/* 收货信息 */}
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-white">收货信息</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>收货人</Label>
                  <Input
                    value={formData.receiver_name}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        receiver_name: e.target.value,
                      })
                    }
                    placeholder="请输入收货人"
                    className="bg-surface-100 border-white/10"
                  />
                </div>
                <div className="space-y-2">
                  <Label>收货电话</Label>
                  <Input
                    value={formData.receiver_phone}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        receiver_phone: e.target.value,
                      })
                    }
                    placeholder="请输入收货电话"
                    className="bg-surface-100 border-white/10"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>收货地址</Label>
                <Textarea
                  value={formData.receiver_address}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      receiver_address: e.target.value,
                    })
                  }
                  placeholder="请输入收货地址"
                  className="bg-surface-100 border-white/10"
                  rows={3}
                />
              </div>
            </div>

            {/* 金额和审批 */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>发货金额 *</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={formData.delivery_amount}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      delivery_amount: e.target.value,
                    })
                  }
                  placeholder="请输入发货金额"
                  className="bg-surface-100 border-white/10"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>特殊审批</Label>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.special_approval}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        special_approval: e.target.checked,
                      })
                    }
                    className="w-4 h-4 rounded border-white/20 bg-surface-100"
                  />
                  <span className="text-sm text-slate-400">需要特殊审批</span>
                </div>
              </div>
            </div>

            {formData.special_approval && (
              <div className="space-y-2">
                <Label>特殊审批原因</Label>
                <Textarea
                  value={formData.special_approval_reason}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      special_approval_reason: e.target.value,
                    })
                  }
                  placeholder="请输入特殊审批原因"
                  className="bg-surface-100 border-white/10"
                  rows={2}
                />
              </div>
            )}

            {/* 备注 */}
            <div className="space-y-2">
              <Label>备注</Label>
              <Textarea
                value={formData.remark}
                onChange={(e) =>
                  setFormData({ ...formData, remark: e.target.value })
                }
                placeholder="请输入备注信息"
                className="bg-surface-100 border-white/10"
                rows={3}
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={submitting}
              >
                取消
              </Button>
              <Button
                type="submit"
                disabled={submitting}
                className="bg-primary hover:bg-primary/90"
              >
                {submitting ? "创建中..." : "创建发货单"}
              </Button>
            </DialogFooter>
          </form>
        </DialogBody>
      </DialogContent>
    </Dialog>
  );
}
