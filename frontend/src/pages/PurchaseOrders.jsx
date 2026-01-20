import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Package,
  Plus,
  Search,
  Filter,
  Download,
  Upload,
  Eye,
  Edit3,
  Trash2,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Truck,
  FileText,
  MoreHorizontal,
  ChevronDown,
  Calendar,
  Building2,
  DollarSign } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody } from
"../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import { Textarea } from "../components/ui/textarea";
import { Label } from "../components/ui/label";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer as _staggerContainer } from "../lib/animations";
import {
  purchaseApi,
  supplierApi,
  projectApi,
  materialApi as _materialApi } from
"../services/api";
import { toast } from "../components/ui/toast";
import { ApiIntegrationError } from "../components/ui";

// 导入重构后的组件
import {
  PurchaseOrdersOverview,
  ORDER_STATUS,
  ORDER_STATUS_CONFIGS,
  ORDER_URGENCY,
  ORDER_URGENCY_CONFIGS,
  PAYMENT_TERMS,
  PAYMENT_TERMS_CONFIGS,
  APPROVAL_STATUS,
  APPROVAL_STATUS_CONFIGS,
  PROCUREMENT_CATEGORIES,
  SHIPPING_METHODS,
  PurchaseOrderUtils } from
"../components/purchase-orders";

function OrderCard({ order, onView, onEdit, onDelete, onSubmit, onApprove }) {
  const status = ORDER_STATUS_CONFIGS[order.status];
  const urgency = ORDER_URGENCY_CONFIGS[order.urgency];
  const StatusIcon = status?.icon ? getIcon(status.icon) : Package;

  function getIcon(iconName) {
    const icons = {
      FileText,
      Clock,
      Truck,
      CheckCircle2,
      AlertTriangle,
      Trash2
    };
    return icons[iconName] || Package;
  }

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      className="bg-surface-1 rounded-xl border border-border p-4 hover:border-border/80 transition-colors">

      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono font-semibold text-white">
              {order.id}
            </span>
            {order.urgency !== "normal" &&
            <Badge
              variant="outline"
              className={cn("text-[10px] border", urgency?.color)}>

                {urgency?.label}
            </Badge>
            }
          </div>
          <p className="text-sm text-slate-400">{order.supplierName}</p>
        </div>
        <Badge className={cn("gap-1", status?.color)}>
          <StatusIcon className="w-3 h-3" />
          {status?.label}
        </Badge>
      </div>

      {/* Project Info */}
      <div className="flex items-center gap-2 mb-3 text-sm">
        <span className="text-accent">{order.projectId}</span>
        <span className="text-slate-500">·</span>
        <span className="text-slate-400 truncate">{order.projectName}</span>
      </div>

      {/* Progress */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-xs mb-1">
          <span className="text-slate-400">到货进度</span>
          <span className="text-white">
            {order.receivedCount}/{order.itemCount} 项
          </span>
        </div>
        <div className="h-1.5 bg-surface-2 rounded-full overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-all",
              order.status === "completed" ?
              "bg-emerald-500" :
              order.status === "delayed" ?
              "bg-red-500" :
              "bg-accent"
            )}
            style={{
              width: `${order.receivedCount / order.itemCount * 100}%`
            }} />

        </div>
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-2 gap-3 mb-3 text-sm">
        <div>
          <span className="text-slate-500 text-xs">订单金额</span>
          <p className="text-white font-medium">
            ¥{(order.totalAmount || 0).toLocaleString()}
          </p>
        </div>
        <div>
          <span className="text-slate-500 text-xs">预计到货</span>
          <p
            className={cn(
              "font-medium",
              order.status === "delayed" ? "text-red-400" : "text-white"
            )}>

            {order.delayedDate || PurchaseOrderUtils.formatDate(order.expected_date)}
          </p>
        </div>
      </div>

      {/* Delay Reason */}
      {order.delayReason &&
      <div className="mb-3 p-2 rounded-lg bg-red-500/10 text-xs text-red-300 flex items-center gap-2">
          <AlertTriangle className="w-3 h-3" />
          {order.delayReason}
      </div>
      }

      {/* Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-border/50">
        <span className="text-xs text-slate-500">采购员：{order.buyer}</span>
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2"
            onClick={() => onView(order)}
            title="查看详情">

            <Eye className="w-3.5 h-3.5" />
          </Button>
          {order.status === ORDER_STATUS.DRAFT && onEdit &&
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2"
            onClick={() => onEdit(order)}
            title="编辑">

              <Edit3 className="w-3.5 h-3.5" />
          </Button>
          }
          {order.status === ORDER_STATUS.DRAFT && onDelete &&
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-red-400 hover:text-red-300"
            onClick={() => onDelete(order)}
            title="删除">

              <Trash2 className="w-3.5 h-3.5" />
          </Button>
          }
          {(order.status === ORDER_STATUS.PENDING || order.status === ORDER_STATUS.PARTIAL_RECEIVED) && onSubmit &&
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-blue-400 hover:text-blue-300"
            onClick={() => onSubmit(order)}
            title="确认收货">

              <CheckCircle2 className="w-3.5 h-3.5" />
          </Button>
          }
          {order.status === ORDER_STATUS.DRAFT && onApprove &&
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-emerald-400 hover:text-emerald-300"
            onClick={() => onApprove(order)}
            title="提交审批">

              <CheckCircle2 className="w-3.5 h-3.5" />
          </Button>
          }
        </div>
      </div>
    </motion.div>);

}

export default function PurchaseOrders() {
  const _navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialStatus = searchParams.get("status") || "all";

  // State
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState(initialStatus);
  const [sortBy, setSortBy] = useState("expected_date");
  const [sortOrder, setSortOrder] = useState("asc");

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [_showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showReceiveModal, setShowReceiveModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);

  // Dropdown data
  const [suppliers, setSuppliers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [_materials, _setMaterials] = useState([]);

  // Form states
  const [newOrder, setNewOrder] = useState({
    supplier_id: "",
    project_id: "",
    items: [],
    payment_terms: PAYMENT_TERMS.NET30,
    shipping_method: SHIPPING_METHODS.STANDARD,
    notes: "",
    urgency: ORDER_URGENCY.NORMAL
  });

  const [editOrder, setEditOrder] = useState({
    id: "",
    supplier_id: "",
    project_id: "",
    items: [],
    payment_terms: PAYMENT_TERMS.NET30,
    shipping_method: SHIPPING_METHODS.STANDARD,
    notes: "",
    urgency: ORDER_URGENCY.NORMAL
  });

  const [receiveData, setReceiveData] = useState({
    received_items: [],
    notes: "",
    received_date: new Date().toISOString().split('T')[0]
  });

  // Load orders
  const loadOrders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page_size: 1000,
        ...(statusFilter && statusFilter !== "all" && { status: statusFilter }),
        ...(searchQuery && { search: searchQuery })
      };

      const response = await purchaseApi.list(params);
      let ordersData = response.data?.data || response.data?.items || response.data || [];

      // 确保 ordersData 是数组
      if (!Array.isArray(ordersData)) {
        ordersData = [];
      }

      // Transform API response to component format
      const transformedOrders = ordersData.map((order) => {
        const items = order.items || [];
        const itemCount = items.length;
        const receivedCount = items.filter(
          (item) => (item.received_qty || 0) >= (item.quantity || 0)
        ).length;

        return {
          id: order.id || order.purchase_order_id || `PO-${Math.random().toString(36).substr(2, 9).toUpperCase()}`,
          supplierId: order.supplier_id || "",
          supplierName: order.supplier_name || order.supplier?.name || "未知供应商",
          projectId: order.project_id || order.project?.id || "",
          projectName: order.project_name || order.project?.name || "",
          status: order.status || ORDER_STATUS.DRAFT,
          urgency: order.urgency || ORDER_URGENCY.NORMAL,
          buyer: order.buyer_name || order.buyer || "",
          createdDate: order.created_date || order.createdAt || "",
          expectedDate: order.expected_date || order.delivery_date || "",
          delayedDate: order.delayed_date || "",
          delayReason: order.delay_reason || "",
          totalAmount: parseFloat(
            order.total_amount || order.amount_with_tax || 0
          ),
          receivedAmount: 0,
          itemCount: itemCount,
          receivedCount: receivedCount,
          items: items.map((item) => ({
            code: item.material_code || "",
            name: item.material_name || "",
            qty: item.quantity || 0,
            price: parseFloat(item.unit_price || 0),
            received: item.received_qty || 0
          })),
          _original: order
        };
      });

      // Calculate received amounts
      transformedOrders.forEach((order) => {
        order.receivedAmount = PurchaseOrderUtils.calculateReceivedAmount(order.items);

        // Check for delayed orders
        if (PurchaseOrderUtils.isOrderDelayed(order.expectedDate, order.status)) {
          order.status = ORDER_STATUS.DELAYED;
          order.delayedDate = PurchaseOrderUtils.formatDate(new Date());
        }
      });

      setOrders(transformedOrders);
    } catch (err) {
      console.error("Failed to load purchase orders:", err);
      setError(err);
      setOrders([]);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, searchQuery]);

  // Initial load
  useEffect(() => {
    loadOrders();
  }, []);

  // Reload when filters change
  useEffect(() => {
    loadOrders();
  }, [loadOrders]);

  // Load dropdown data
  useEffect(() => {
    const loadDropdownData = async () => {
      try {
        const [suppliersRes, projectsRes] = await Promise.all([
        supplierApi.list({ page_size: 1000 }),
        projectApi.list({ page_size: 1000 })]
        );

        const suppliersData =
        suppliersRes.data?.items || suppliersRes.data || [];
        const projectsData = projectsRes.data?.items || projectsRes.data || [];

        setSuppliers(suppliersData);
        setProjects(projectsData);
      } catch (err) {
        console.error("Failed to load dropdown data:", err);
        setSuppliers([]);
        setProjects([]);
      }
    };

    loadDropdownData();
  }, []);

  // Client-side filtering and sorting
  const filteredOrders = PurchaseOrderUtils.searchOrders(orders, searchQuery);
  const sortedOrders = PurchaseOrderUtils.sortOrders(filteredOrders, sortBy, sortOrder);

  // Calculate stats
  const _stats = {
    total: orders.length,
    pending: orders.filter((o) => o.status === ORDER_STATUS.PENDING).length,
    delayed: orders.filter((o) => o.status === ORDER_STATUS.DELAYED).length,
    totalAmount: orders.reduce((sum, o) => sum + (o.totalAmount || 0), 0)
  };

  // Event handlers
  const handleCreateOrder = async () => {
    try {
      const errors = PurchaseOrderUtils.validateOrder(newOrder);
      if (errors.length > 0) {
        toast.error(errors.join(", "));
        return;
      }

      const orderData = {
        ...newOrder,
        id: PurchaseOrderUtils.generateOrderNumber(),
        total_amount: PurchaseOrderUtils.calculateOrderTotal(newOrder.items),
        expected_date: newOrder.expected_date
      };

      await purchaseApi.create(orderData);
      toast.success("采购订单创建成功");
      setShowCreateModal(false);
      setNewOrder({
        supplier_id: "",
        project_id: "",
        items: [],
        payment_terms: PAYMENT_TERMS.NET30,
        shipping_method: SHIPPING_METHODS.STANDARD,
        notes: "",
        urgency: ORDER_URGENCY.NORMAL
      });
      loadOrders();
    } catch (err) {
      console.error("Failed to create order:", err);
      toast.error("创建采购订单失败");
    }
  };

  const _handleEditOrder = async () => {
    try {
      const errors = PurchaseOrderUtils.validateOrder(editOrder);
      if (errors.length > 0) {
        toast.error(errors.join(", "));
        return;
      }

      const orderData = {
        ...editOrder,
        total_amount: PurchaseOrderUtils.calculateOrderTotal(editOrder.items)
      };

      await purchaseApi.update(editOrder.id, orderData);
      toast.success("采购订单更新成功");
      setShowEditModal(false);
      loadOrders();
    } catch (err) {
      console.error("Failed to update order:", err);
      toast.error("更新采购订单失败");
    }
  };

  const handleDeleteOrder = async () => {
    try {
      await purchaseApi.delete(selectedOrder.id);
      toast.success("采购订单删除成功");
      setShowDeleteModal(false);
      setSelectedOrder(null);
      loadOrders();
    } catch (err) {
      console.error("Failed to delete order:", err);
      toast.error("删除采购订单失败");
    }
  };

  const handleSubmitApproval = async () => {
    try {
      await purchaseApi.submitApproval(selectedOrder.id);
      toast.success("采购订单已提交审批");
      setShowDetailModal(false);
      setSelectedOrder(null);
      loadOrders();
    } catch (err) {
      console.error("Failed to submit approval:", err);
      toast.error("提交审批失败");
    }
  };

  const handleReceiveGoods = async () => {
    try {
      await purchaseApi.receiveGoods(selectedOrder.id, receiveData);
      toast.success("收货确认成功");
      setShowReceiveModal(false);
      setSelectedOrder(null);
      setReceiveData({
        received_items: [],
        notes: "",
        received_date: new Date().toISOString().split('T')[0]
      });
      loadOrders();
    } catch (err) {
      console.error("Failed to receive goods:", err);
      toast.error("收货确认失败");
    }
  };

  const handleExportData = () => {
    const csvData = sortedOrders.map((order) => ({
      "订单编号": order.id,
      "供应商": order.supplierName,
      "项目": order.projectName,
      "状态": ORDER_STATUS_CONFIGS[order.status]?.label,
      "金额": order.totalAmount,
      "采购员": order.buyer,
      "预计到货": order.expectedDate
    }));

    const csv = [
    Object.keys(csvData[0]).join(","),
    ...csvData.map((row) => Object.values(row).join(","))].
    join("\n");

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `采购订单_${new Date().toISOString().split("T")[0]}.csv`;
    link.click();
  };

  // Loading and error states
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4" />
          <p className="text-text-secondary">加载采购订单...</p>
        </div>
      </div>);

  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <ApiIntegrationError
          error={error}
          onRetry={loadOrders}
          title="加载采购订单失败"
          description="无法获取采购订单数据，请检查网络连接后重试" />

      </div>);

  }

  return (
    <div className="min-h-screen bg-background">
      <PageHeader
        title="采购订单管理"
        description="管理采购订单、供应商、审批流程和收货确认" />


      <div className="container mx-auto px-4 py-6">
        {/* Overview Section */}
        <PurchaseOrdersOverview orders={orders} />

        {/* Controls Section */}
        <Card className="bg-surface-1 border-border mb-6">
          <CardContent className="p-4">
            <div className="flex flex-col lg:flex-row gap-4 items-center">
              {/* Search */}
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary" />
                  <Input
                    placeholder="搜索订单编号、供应商..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 bg-surface-2 border-border" />

                </div>
              </div>

              {/* Filters */}
              <div className="flex gap-2">
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-40 bg-surface-2 border-border">
                    <SelectValue placeholder="订单状态" />
                  </SelectTrigger>
                  <SelectContent className="bg-surface-2 border-border">
                    <SelectItem value="all">全部状态</SelectItem>
                    {Object.entries(ORDER_STATUS_CONFIGS).map(([key, config]) =>
                    <SelectItem key={key} value={key}>
                        {config.label}
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>

                <Select value={sortBy} onValueChange={setSortBy}>
                  <SelectTrigger className="w-32 bg-surface-2 border-border">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-surface-2 border-border">
                    <SelectItem value="expected_date">到货日期</SelectItem>
                    <SelectItem value="totalAmount">订单金额</SelectItem>
                    <SelectItem value="createdDate">创建日期</SelectItem>
                  </SelectContent>
                </Select>

                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
                  className="bg-surface-2 border-border">

                  <ChevronDown
                    className={cn(
                      "h-4 w-4 transition-transform",
                      sortOrder === "asc" && "rotate-180"
                    )} />

                </Button>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={handleExportData}
                  className="bg-surface-2 border-border">

                  <Download className="h-4 w-4 mr-2" />
                  导出
                </Button>
                <Button
                  onClick={() => setShowCreateModal(true)}
                  className="bg-accent hover:bg-accent/90">

                  <Plus className="h-4 w-4 mr-2" />
                  新建订单
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Orders Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <AnimatePresence>
            {sortedOrders.map((order) =>
            <motion.div
              key={order.id}
              initial="hidden"
              animate="visible"
              exit="hidden"
              variants={fadeIn}
              layout>

                <OrderCard
                order={order}
                onView={(order) => {
                  setSelectedOrder(order);
                  setShowDetailModal(true);
                }}
                onEdit={(order) => {
                  setSelectedOrder(order);
                  setEditOrder({
                    ...order,
                    payment_terms: order.paymentTerms || PAYMENT_TERMS.NET30,
                    shipping_method: order.shippingMethod || SHIPPING_METHODS.STANDARD
                  });
                  setShowEditModal(true);
                }}
                onDelete={(order) => {
                  setSelectedOrder(order);
                  setShowDeleteModal(true);
                }}
                onSubmit={(order) => {
                  setSelectedOrder(order);
                  setShowReceiveModal(true);
                }}
                onApprove={(order) => {
                  setSelectedOrder(order);
                  handleSubmitApproval();
                }} />

            </motion.div>
            )}
          </AnimatePresence>
        </div>

        {sortedOrders.length === 0 && !loading &&
        <div className="text-center py-12">
            <Package className="h-16 w-16 text-text-secondary mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-medium text-white mb-2">暂无采购订单</h3>
            <p className="text-text-secondary mb-4">还没有创建任何采购订单</p>
            <Button onClick={() => setShowCreateModal(true)} className="bg-accent hover:bg-accent/90">
              <Plus className="h-4 w-4 mr-2" />
              创建第一个采购订单
            </Button>
        </div>
        }

        {/* Create Order Modal */}
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogContent className="sm:max-w-[700px] bg-surface-1 border-border">
            <DialogHeader>
              <DialogTitle className="text-white">创建采购订单</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-text-secondary">供应商</Label>
                  <Select
                    value={newOrder.supplier_id}
                    onValueChange={(value) =>
                    setNewOrder({ ...newOrder, supplier_id: value })
                    }>

                    <SelectTrigger className="bg-surface-2 border-border">
                      <SelectValue placeholder="选择供应商" />
                    </SelectTrigger>
                    <SelectContent className="bg-surface-2 border-border">
                      {suppliers.map((supplier) =>
                      <SelectItem key={supplier.id} value={supplier.id}>
                          {supplier.name}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-text-secondary">项目</Label>
                  <Select
                    value={newOrder.project_id}
                    onValueChange={(value) =>
                    setNewOrder({ ...newOrder, project_id: value })
                    }>

                    <SelectTrigger className="bg-surface-2 border-border">
                      <SelectValue placeholder="选择项目" />
                    </SelectTrigger>
                    <SelectContent className="bg-surface-2 border-border">
                      {projects.map((project) =>
                      <SelectItem key={project.id} value={project.id}>
                          {project.name}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-text-secondary">支付条款</Label>
                  <Select
                    value={newOrder.payment_terms}
                    onValueChange={(value) =>
                    setNewOrder({ ...newOrder, payment_terms: value })
                    }>

                    <SelectTrigger className="bg-surface-2 border-border">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-surface-2 border-border">
                      {Object.entries(PAYMENT_TERMS_CONFIGS).map(([key, config]) =>
                      <SelectItem key={key} value={key}>
                          {config.label}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-text-secondary">运输方式</Label>
                  <Select
                    value={newOrder.shipping_method}
                    onValueChange={(value) =>
                    setNewOrder({ ...newOrder, shipping_method: value })
                    }>

                    <SelectTrigger className="bg-surface-2 border-border">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-surface-2 border-border">
                      {Object.entries(SHIPPING_METHODS).map(([key, config]) =>
                      <SelectItem key={key} value={key}>
                          {config.label}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label className="text-text-secondary">备注</Label>
                <Textarea
                  value={newOrder.notes}
                  onChange={(e) =>
                  setNewOrder({ ...newOrder, notes: e.target.value })
                  }
                  placeholder="订单备注信息..."
                  className="bg-surface-2 border-border" />

              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowCreateModal(false)}
                className="bg-surface-2 border-border">

                取消
              </Button>
              <Button onClick={handleCreateOrder} className="bg-accent hover:bg-accent/90">
                创建订单
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Detail Modal */}
        <Dialog open={showDetailModal} onOpenChange={setShowDetailModal}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-surface-1 border-border">
            <DialogHeader>
              <DialogTitle className="text-white">采购订单详情</DialogTitle>
            </DialogHeader>
            {selectedOrder &&
            <div className="space-y-6">
                {/* Order Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-text-secondary">订单编号</Label>
                    <p className="text-white font-mono">{selectedOrder.id}</p>
                  </div>
                  <div>
                    <Label className="text-text-secondary">供应商</Label>
                    <p className="text-white">{selectedOrder.supplierName}</p>
                  </div>
                  <div>
                    <Label className="text-text-secondary">项目</Label>
                    <p className="text-white">{selectedOrder.projectName}</p>
                  </div>
                  <div>
                    <Label className="text-text-secondary">状态</Label>
                    <Badge className={ORDER_STATUS_CONFIGS[selectedOrder.status]?.color}>
                      {ORDER_STATUS_CONFIGS[selectedOrder.status]?.label}
                    </Badge>
                  </div>
                  <div>
                    <Label className="text-text-secondary">采购员</Label>
                    <p className="text-white">{selectedOrder.buyer}</p>
                  </div>
                  <div>
                    <Label className="text-text-secondary">创建日期</Label>
                    <p className="text-white">{PurchaseOrderUtils.formatDate(selectedOrder.createdDate)}</p>
                  </div>
                  <div>
                    <Label className="text-text-secondary">预计到货</Label>
                    <p className="text-white">{PurchaseOrderUtils.formatDate(selectedOrder.expectedDate)}</p>
                  </div>
                  <div>
                    <Label className="text-text-secondary">订单金额</Label>
                    <p className="text-white font-semibold">
                      ¥{PurchaseOrderUtils.formatCurrency(selectedOrder.totalAmount)}
                    </p>
                  </div>
                </div>

                {/* Items Table */}
                <div>
                  <Label className="text-text-secondary mb-2 block">采购项目</Label>
                  <div className="bg-surface-2 rounded-lg overflow-hidden">
                    <table className="w-full">
                      <thead className="bg-surface-3">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-text-secondary">物料编码</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-text-secondary">物料名称</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-text-secondary">数量</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-text-secondary">单价</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-text-secondary">小计</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-text-secondary">已收货</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {selectedOrder.items?.map((item, index) =>
                      <tr key={index}>
                            <td className="px-4 py-2 text-sm text-white">{item.code}</td>
                            <td className="px-4 py-2 text-sm text-white">{item.name}</td>
                            <td className="px-4 py-2 text-sm text-white text-right">{item.qty}</td>
                            <td className="px-4 py-2 text-sm text-white text-right">
                              ¥{PurchaseOrderUtils.formatCurrency(item.price)}
                            </td>
                            <td className="px-4 py-2 text-sm text-white text-right">
                              ¥{PurchaseOrderUtils.formatCurrency(item.qty * item.price)}
                            </td>
                            <td className="px-4 py-2 text-sm text-white text-right">{item.received}</td>
                      </tr>
                      )}
                      </tbody>
                    </table>
                  </div>
                </div>
            </div>
            }
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowDetailModal(false)}
                className="bg-surface-2 border-border">

                关闭
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Modal */}
        <Dialog open={showDeleteModal} onOpenChange={setShowDeleteModal}>
          <DialogContent className="bg-surface-1 border-border">
            <DialogHeader>
              <DialogTitle className="text-white">确认删除</DialogTitle>
            </DialogHeader>
            <div className="text-center py-4">
              <AlertTriangle className="h-12 w-12 text-red-400 mx-auto mb-4" />
              <p className="text-white mb-2">确定要删除采购订单 {selectedOrder?.id} 吗？</p>
              <p className="text-text-secondary text-sm">此操作不可撤销</p>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowDeleteModal(false)}
                className="bg-surface-2 border-border">

                取消
              </Button>
              <Button
                variant="destructive"
                onClick={handleDeleteOrder}
                className="bg-red-500 hover:bg-red-600">

                确认删除
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Receive Goods Modal */}
        <Dialog open={showReceiveModal} onOpenChange={setShowReceiveModal}>
          <DialogContent className="bg-surface-1 border-border">
            <DialogHeader>
              <DialogTitle className="text-white">确认收货</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label className="text-text-secondary">收货日期</Label>
                <Input
                  type="date"
                  value={receiveData.received_date}
                  onChange={(e) =>
                  setReceiveData({ ...receiveData, received_date: e.target.value })
                  }
                  className="bg-surface-2 border-border" />

              </div>
              <div>
                <Label className="text-text-secondary">收货备注</Label>
                <Textarea
                  value={receiveData.notes}
                  onChange={(e) =>
                  setReceiveData({ ...receiveData, notes: e.target.value })
                  }
                  placeholder="收货情况说明..."
                  className="bg-surface-2 border-border" />

              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowReceiveModal(false)}
                className="bg-surface-2 border-border">

                取消
              </Button>
              <Button onClick={handleReceiveGoods} className="bg-accent hover:bg-accent/90">
                确认收货
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>);

}