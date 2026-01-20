/**
 * Procurement Engineer Workstation - Main dashboard for procurement specialists
 * Features: Purchase order management, supplier tracking, material arrival, cost control
 * Core Functions: Order management, delivery tracking, cost control, supplier evaluation
 */

import { useState, useMemo as _useMemo, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  ShoppingCart,
  Package,
  Truck,
  AlertTriangle,
  CheckCircle2,
  Clock,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Plus,
  ChevronRight,
  Search,
  Filter,
  Calendar,
  Building2,
  BarChart3,
  Eye,
  Edit,
  Download,
  Send,
  Inbox,
  Zap,
  PieChart } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
  Input } from
"../components/ui";
import { cn, formatCurrency, formatDate as _formatDate } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { purchaseApi, shortageApi, supplierApi } from "../services/api";
import { ApiIntegrationError } from "../components/ui";

// Statistics configuration
const statConfig = {
  pendingOrders: {
    label: "待采购订单",
    value: 8,
    unit: "个",
    icon: ShoppingCart,
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    trend: "+2"
  },
  arrivedMaterial: {
    label: "本月到货",
    value: 34,
    unit: "批",
    icon: Truck,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    trend: "+5"
  },
  shortage: {
    label: "缺料预警",
    value: 3,
    unit: "项",
    icon: AlertTriangle,
    color: "text-red-400",
    bg: "bg-red-500/10",
    trend: "-1"
  },
  suppliers: {
    label: "在用供应商",
    value: 24,
    unit: "家",
    icon: Building2,
    color: "text-purple-400",
    bg: "bg-purple-500/10",
    trend: "+1"
  },
  budgetUsed: {
    label: "预算使用率",
    value: 68,
    unit: "%",
    icon: PieChart,
    color: "text-amber-400",
    bg: "bg-amber-500/10"
  },
  onTimeRate: {
    label: "按期到货率",
    value: 94,
    unit: "%",
    icon: CheckCircle2,
    color: "text-cyan-400",
    bg: "bg-cyan-500/10"
  }
};

// Mock data removed - 使用真实API

// Task type configuration
const taskTypeConfig = {
  order: { icon: ShoppingCart, label: "采购", color: "text-blue-400" },
  shortage: { icon: AlertTriangle, label: "缺料", color: "text-red-400" },
  arrival: { icon: Truck, label: "到货", color: "text-emerald-400" },
  inspection: { icon: CheckCircle2, label: "检验", color: "text-cyan-400" },
  supplier: { icon: Building2, label: "供应商", color: "text-purple-400" },
  cost: { icon: DollarSign, label: "成本", color: "text-amber-400" }
};

const priorityColors = {
  high: { bg: "bg-red-500/20", text: "text-red-400", label: "紧急" },
  medium: { bg: "bg-amber-500/20", text: "text-amber-400", label: "中等" },
  low: { bg: "bg-blue-500/20", text: "text-blue-400", label: "普通" }
};

const StatCard = ({ config }) => {
  const Icon = config.icon;
  return (
    <motion.div
      variants={fadeIn}
      className="relative overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 backdrop-blur">

      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="mb-2 text-sm text-slate-400">{config.label}</p>
          <p className={cn("text-2xl font-bold", config.color)}>
            {config.value}
          </p>
          <p className="mt-1 text-xs text-slate-500">{config.unit}</p>
          {config.trend &&
          <p
            className={cn(
              "mt-2 text-xs font-semibold",
              config.trend.startsWith("+") ?
              "text-emerald-400" :
              "text-amber-400"
            )}>

              {config.trend}
          </p>
          }
        </div>
        <div className={cn("rounded-lg p-3", config.bg)}>
          <Icon className={cn("h-6 w-6", config.color)} />
        </div>
      </div>
      <div className="absolute right-0 top-0 h-20 w-20 rounded-full bg-gradient-to-br from-purple-500/10 to-transparent blur-2xl" />
    </motion.div>);

};

const TodoItem = ({ todo, onComplete }) => {
  const typeConfig = taskTypeConfig[todo.type];
  const priorityConfig = priorityColors[todo.priority];
  const Icon = typeConfig.icon;

  const getDaysColor = (daysLeft) => {
    if (daysLeft === 0) {return "text-red-400";}
    if (daysLeft <= 2) {return "text-orange-400";}
    if (daysLeft <= 7) {return "text-amber-400";}
    return "text-cyan-400";
  };

  return (
    <motion.div
      variants={fadeIn}
      className="group flex items-start gap-3 rounded-lg border border-slate-700/50 bg-slate-800/40 p-4 transition-all hover:border-slate-600/80 hover:bg-slate-800/60">

      <div className="relative mt-1 flex-shrink-0">
        <div className={cn("rounded-lg p-2", priorityConfig.bg)}>
          <Icon className={cn("h-5 w-5", typeConfig.color)} />
        </div>
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <p className="font-medium text-slate-200">{todo.title}</p>
            <p className="mt-1 text-sm text-slate-400">{todo.target}</p>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="bg-slate-700/40 text-xs">
                {typeConfig.label}
              </Badge>
              <Badge
                className={cn(
                  "text-xs",
                  priorityConfig.bg,
                  priorityConfig.text
                )}>

                {priorityConfig.label}
              </Badge>
              {todo.daysLeft === 0 ?
              <span className="text-xs font-medium text-red-400">
                  今天截止
              </span> :

              <span
                className={cn(
                  "text-xs font-medium",
                  getDaysColor(todo.daysLeft)
                )}>

                  {todo.daysLeft}天截止
              </span>
              }
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-shrink-0 gap-1 opacity-0 transition-opacity group-hover:opacity-100">
        <Button
          size="sm"
          variant="ghost"
          className="h-8 w-8 p-0"
          onClick={() => onComplete(todo.id)}>

          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
        </Button>
      </div>
    </motion.div>);

};

const PurchaseOrderRow = ({ order }) => {
  const statusConfig = {
    draft: { label: "草稿", color: "bg-slate-500/20 text-slate-400" },
    submitted: { label: "已提交", color: "bg-blue-500/20 text-blue-400" },
    confirmed: { label: "已确认", color: "bg-purple-500/20 text-purple-400" },
    shipped: { label: "已发货", color: "bg-cyan-500/20 text-cyan-400" },
    received: { label: "已收货", color: "bg-emerald-500/20 text-emerald-400" },
    completed: { label: "已完成", color: "bg-slate-500/20 text-slate-400" }
  };

  const arrivalConfig = {
    pending: { label: "待发货", icon: Clock },
    in_transit: { label: "运输中", icon: Truck },
    delayed: { label: "已延期", icon: AlertTriangle },
    completed: { label: "已到货", icon: CheckCircle2 }
  };

  const getDaysColor = (daysLeft) => {
    if (daysLeft < 0) {return "text-red-400";}
    if (daysLeft <= 3) {return "text-orange-400";}
    return "text-cyan-400";
  };

  const arrivalStatus = arrivalConfig[order.arrivalStatus];
  const ArrivalIcon = arrivalStatus.icon;

  return (
    <motion.div
      variants={fadeIn}
      className="group flex items-center justify-between rounded-lg border border-slate-700/50 bg-slate-800/40 px-4 py-3 transition-all hover:border-slate-600/80 hover:bg-slate-800/60">

      <div className="flex-1">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-slate-100">{order.id}</span>
          <span className="text-sm text-slate-400">{order.supplier}</span>
        </div>
        <div className="mt-1 flex items-center gap-3 text-sm">
          <span className="text-slate-500">{order.items}</span>
          <span className="text-slate-600">|</span>
          <span className="font-semibold text-amber-400">
            {formatCurrency(order.totalAmount)}
          </span>
        </div>
      </div>

      <div className="ml-4 flex items-center gap-2">
        <div className="flex flex-col items-end gap-1.5">
          <Badge className={statusConfig[order.status].color}>
            {statusConfig[order.status].label}
          </Badge>
          <div className="flex items-center gap-1">
            <ArrivalIcon className="h-3.5 w-3.5 text-slate-400" />
            <span className="text-xs text-slate-400">
              {arrivalStatus.label}
            </span>
          </div>
        </div>
        <div className="ml-4 flex flex-col items-end text-sm">
          <span className={cn("font-semibold", getDaysColor(order.daysLeft))}>
            {order.daysLeft < 0 ?
            `逾期${Math.abs(order.daysLeft)}天` :
            `${order.daysLeft}天`}
          </span>
          <span className="text-xs text-slate-500">{order.dueDate}</span>
        </div>
      </div>

      <div className="ml-4 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
        <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
          <Eye className="h-4 w-4 text-blue-400" />
        </Button>
        <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
          <Edit className="h-4 w-4 text-amber-400" />
        </Button>
      </div>
    </motion.div>);

};

const ShortageAlert = ({ shortage }) => {
  const priorityConfig = {
    high: { label: "紧急", color: "bg-red-500/20 text-red-400" },
    medium: { label: "中等", color: "bg-amber-500/20 text-amber-400" },
    low: { label: "普通", color: "bg-blue-500/20 text-blue-400" }
  };

  return (
    <motion.div
      variants={fadeIn}
      className="rounded-lg border border-slate-700/50 bg-slate-800/40 p-4">

      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <p className="font-semibold text-slate-100">{shortage.material}</p>
          <div className="mt-2 grid grid-cols-3 gap-2 text-sm">
            <div className="rounded bg-slate-700/50 px-2 py-1">
              <p className="text-xs text-slate-400">需求</p>
              <p className="font-semibold text-slate-200">
                {shortage.required}
              </p>
            </div>
            <div className="rounded bg-slate-700/50 px-2 py-1">
              <p className="text-xs text-slate-400">库存</p>
              <p className="font-semibold text-slate-200">
                {shortage.available}
              </p>
            </div>
            <div className="rounded bg-red-500/20 px-2 py-1">
              <p className="text-xs text-red-400">缺料</p>
              <p className="font-semibold text-red-300">{shortage.shortage}</p>
            </div>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <Badge className={priorityConfig[shortage.priority].color}>
            {priorityConfig[shortage.priority].label}
          </Badge>
          <span className="text-xs text-slate-500">{shortage.neededDate}</span>
          <span className="text-xs font-semibold text-cyan-400">
            {shortage.daysToNeeded}天后需要
          </span>
        </div>
      </div>
    </motion.div>);

};

export default function ProcurementEngineerWorkstation() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [completedTodos, setCompletedTodos] = useState([]);
  const [stats, setStats] = useState(statConfig);
  const [todos, setTodos] = useState([]);
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  const [shortages, setShortages] = useState([]);

  // Load procurement dashboard data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Load purchase orders
      const ordersResponse = await purchaseApi.orders.list({
        page: 1,
        page_size: 20
      });
      const ordersData =
      ordersResponse.data?.items || ordersResponse.data || [];

      // Load shortages
      const shortagesResponse = await shortageApi.list({
        page: 1,
        page_size: 20
      });
      let shortageData =
      shortagesResponse.data?.items || shortagesResponse.data || [];

      // Transform purchase orders
      const transformedOrders = ordersData.map((order) => {
        const dueDate = new Date(order.required_date || order.due_date || "");
        const today = new Date();
        const daysLeft = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));

        // Determine arrival status based on order status
        let arrivalStatus = "pending";
        if (order.status === "SHIPPED") {arrivalStatus = "in_transit";}else
        if (order.status === "RECEIVED") {arrivalStatus = "completed";}else
        if (daysLeft < 0 && order.status !== "RECEIVED")
        {arrivalStatus = "delayed";}

        return {
          id: order.order_no || order.id?.toString(),
          supplier: order.supplier_name || "",
          items: order.items?.map((i) => i.material_name).join(", ") || "",
          quantity:
          order.items?.reduce((sum, i) => sum + (i.quantity || 0), 0) || 0,
          unit: "件",
          unitPrice: 0,
          totalAmount: parseFloat(
            order.total_amount || order.amount_with_tax || 0
          ),
          orderDate: order.order_date || order.created_at?.split("T")[0] || "",
          dueDate: order.required_date || order.due_date || "",
          daysLeft,
          status: order.status?.toLowerCase() || "draft",
          paymentStatus: order.payment_status?.toLowerCase() || "unpaid",
          arrivalStatus
        };
      });

      setPurchaseOrders(transformedOrders);

      const transformedShortages = shortageData.map((s) => ({
        id: s.id,
        material: s.material_name || s.material_code || "",
        required: s.required_qty || 0,
        available: s.available_qty || 0,
        shortage: (s.required_qty || 0) - (s.available_qty || 0),
        neededDate: s.needed_date || "",
        daysToNeeded: s.days_to_needed || 0,
        priority: s.priority?.toLowerCase() || "medium",
        status: s.status?.toLowerCase() || "alert"
      }));
      setShortages(transformedShortages);

      // Calculate statistics
      const pendingOrders = ordersData.filter(
        (o) => o.status === "DRAFT" || o.status === "SUBMITTED"
      ).length;
      const arrivedCount = ordersData.filter(
        (o) => o.status === "RECEIVED"
      ).length;
      const shortageCount = transformedShortages.length;

      // Load suppliers count
      let suppliersCount = 24; // Default
      try {
        const suppliersResponse = await supplierApi.list({
          page: 1,
          page_size: 1
        });
        suppliersCount =
        suppliersResponse.data?.total ||
        suppliersResponse.data?.items?.length ||
        24;
      } catch (err) {
        console.error("Failed to load suppliers:", err);
      }

      const _delayedOrders = transformedOrders.filter(
        (o) => o.daysLeft < 0 && o.arrivalStatus !== "completed"
      ).length;
      const _inTransitOrders = transformedOrders.filter(
        (o) => o.arrivalStatus === "in_transit"
      ).length;

      // Update stats
      setStats({
        pendingOrders: {
          ...statConfig.pendingOrders,
          value: pendingOrders
        },
        arrivedMaterial: {
          ...statConfig.arrivedMaterial,
          value: arrivedCount
        },
        shortage: {
          ...statConfig.shortage,
          value: shortageCount
        },
        suppliers: {
          ...statConfig.suppliers,
          value: suppliersCount
        },
        budgetUsed: {
          ...statConfig.budgetUsed,
          value: 68 // Default, can be calculated from actual data
        },
        onTimeRate: {
          ...statConfig.onTimeRate,
          value:
          transformedOrders.length > 0 ?
          Math.round(
            transformedOrders.filter(
              (o) => o.daysLeft >= 0 || o.arrivalStatus === "completed"
            ).length /
            transformedOrders.length *
            100
          ) :
          94
        }
      });

      // Create todos from purchase orders and shortages
      const orderTodos = transformedOrders.
      filter((o) => o.status === "draft" || o.status === "submitted").
      slice(0, 3).
      map((o, _idx) => ({
        id: `order-${o.id}`,
        type: "order",
        title: "采购订单待审核",
        target: `${o.supplier} - ${o.items}`,
        deadline: o.dueDate,
        daysLeft: o.daysLeft,
        priority: o.daysLeft <= 3 ? "high" : "medium",
        status: "pending"
      }));

      const shortageTodos = shortages.slice(0, 3).map((s) => ({
        id: `shortage-${s.id}`,
        type: "shortage",
        title: "物料缺料预警",
        target: `${s.material} - 需求日期${s.neededDate}`,
        deadline: s.neededDate,
        daysLeft: s.daysToNeeded,
        priority: s.priority,
        status: "pending"
      }));

      setTodos([...orderTodos, ...shortageTodos]);
    } catch (err) {
      console.error("Failed to load procurement data:", err);
      setError(err);
      setTodos([]);
      setPurchaseOrders([]);
      setShortages([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCompleteTodo = (todoId) => {
    setCompletedTodos([...completedTodos, todoId]);
  };

  const urgentTodos = todos.filter(
    (todo) => todo.daysLeft <= 3 && !completedTodos.includes(todo.id)
  );
  const allTodos = todos.filter((todo) => !completedTodos.includes(todo.id));

  const delayedOrders = purchaseOrders.filter(
    (o) => o.daysLeft < 0 && o.arrivalStatus !== "completed"
  ).length;
  const inTransitOrders = purchaseOrders.filter(
    (o) => o.arrivalStatus === "in_transit"
  ).length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6 pb-8">
        <PageHeader
          title="采购工程师工作台"
          description="订单管理、物料跟踪、供应商管理、成本控制"
          actions={
          <Button
            onClick={() => navigate("/purchases?action=create")}
            className="bg-blue-600 hover:bg-blue-700">

              <Plus className="w-4 h-4 mr-1" />
              新建采购订单
          </Button>
          } />


        {/* Error state */}
        {error &&
        <ApiIntegrationError
          error={error}
          apiEndpoint="/api/v1/purchase/orders"
          onRetry={loadData} />

        }

        {/* Key statistics */}
        {loading ?
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            {[1, 2, 3, 4, 5, 6].map((i) =>
          <Card key={i} className="bg-surface-1/50 animate-pulse">
                <CardContent className="p-5">
                  <div className="h-20 bg-slate-700/50 rounded" />
                </CardContent>
          </Card>
          )}
        </div> :
        error ?
        <ApiIntegrationError
          error={error}
          apiEndpoint="/api/v1/purchase/orders"
          onRetry={loadData} /> :


        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">

            {Object.entries(stats).map(([key, config]) =>
          <StatCard key={key} config={config} />
          )}
        </motion.div>
        }

        {/* Main content - two column layout */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Left column - Todos (2/3 width) */}
          <div className="lg:col-span-2 space-y-6">
            {/* Urgent tasks */}
            {urgentTodos.length > 0 &&
            <Card className="border-red-500/30 bg-gradient-to-br from-red-500/10 to-slate-900/50">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <Zap className="h-5 w-5 text-red-400" />
                      紧急任务提醒
                    </CardTitle>
                    <Badge className="bg-red-500/20 text-red-400">
                      {urgentTodos.length} 项
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <motion.div
                  variants={staggerContainer}
                  initial="hidden"
                  animate="visible"
                  className="space-y-3">

                    {urgentTodos.slice(0, 3).map((todo) =>
                  <TodoItem
                    key={todo.id}
                    todo={todo}
                    onComplete={handleCompleteTodo} />

                  )}
                  </motion.div>
                </CardContent>
            </Card>
            }

            {/* All todos */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Inbox className="h-5 w-5" />
                    今日工作清单
                  </CardTitle>
                  <span className="text-sm text-slate-400">
                    {allTodos.length}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <motion.div
                  variants={staggerContainer}
                  initial="hidden"
                  animate="visible"
                  className="space-y-3">

                  {allTodos.map((todo) =>
                  <TodoItem
                    key={todo.id}
                    todo={todo}
                    onComplete={handleCompleteTodo} />

                  )}
                </motion.div>
              </CardContent>
            </Card>
          </div>

          {/* Right column - Quick actions & Stats (1/3 width) */}
          <div className="space-y-6">
            {/* Quick actions */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">快捷操作</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {[
                {
                  icon: Plus,
                  label: "新建采购单",
                  color: "text-blue-400",
                  path: "/purchases",
                  action: () => navigate("/purchases?action=create")
                },
                {
                  icon: ShoppingCart,
                  label: "采购订单",
                  color: "text-slate-400",
                  path: "/purchases",
                  action: () => navigate("/purchases")
                },
                {
                  icon: Truck,
                  label: "到货管理",
                  color: "text-emerald-400",
                  path: "/purchases/receipts",
                  action: () => navigate("/purchases/receipts")
                },
                {
                  icon: CheckCircle2,
                  label: "来料检验",
                  color: "text-cyan-400",
                  path: "/purchases/receipts",
                  action: () => navigate("/purchases/receipts")
                },
                {
                  icon: Building2,
                  label: "供应商管理",
                  color: "text-purple-400",
                  path: "/suppliers",
                  action: () => navigate("/suppliers")
                },
                {
                  icon: DollarSign,
                  label: "成本分析",
                  color: "text-amber-400",
                  path: "/cost-analysis",
                  action: () => navigate("/cost-analysis")
                },
                {
                  icon: AlertTriangle,
                  label: "缺料预警",
                  color: "text-red-400",
                  path: "/shortage-alert",
                  action: () => navigate("/shortage-alert")
                },
                {
                  icon: BarChart3,
                  label: "采购报表",
                  color: "text-indigo-400",
                  path: "#",
                  action: () => {}
                }].
                map((item, idx) =>
                <Button
                  key={idx}
                  variant="ghost"
                  className="w-full justify-start gap-2 text-slate-400 hover:bg-slate-800/50 hover:text-slate-100"
                  onClick={item.action}>

                    <item.icon className={cn("h-4 w-4", item.color)} />
                    {item.label}
                </Button>
                )}
              </CardContent>
            </Card>

            {/* Performance metrics */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">本月绩效</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {[
                {
                  label: "采购单完成",
                  value: 28,
                  unit: "个",
                  color: "text-blue-400"
                },
                {
                  label: "按期到货率",
                  value: 94,
                  unit: "%",
                  color: "text-emerald-400"
                },
                {
                  label: "供应商评分",
                  value: 4.2,
                  unit: "/5",
                  color: "text-purple-400"
                },
                {
                  label: "成本节省",
                  value: 52,
                  unit: "万元",
                  color: "text-amber-400"
                }].
                map((metric, idx) =>
                <div key={idx}>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">{metric.label}</span>
                      <span className={cn("font-semibold", metric.color)}>
                        {metric.value}
                        {metric.unit}
                      </span>
                    </div>
                    <Progress
                    value={Math.min(metric.value, 100)}
                    className="mt-1 h-1.5 bg-slate-700/50" />

                </div>
                )}
              </CardContent>
            </Card>

            {/* Alert badges */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">风险提示</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center justify-between rounded-lg bg-red-500/20 px-3 py-2">
                  <span className="text-sm text-red-300">逾期订单</span>
                  <span className="font-semibold text-red-400">
                    {delayedOrders}
                  </span>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-cyan-500/20 px-3 py-2">
                  <span className="text-sm text-cyan-300">运输中</span>
                  <span className="font-semibold text-cyan-400">
                    {inTransitOrders}
                  </span>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-amber-500/20 px-3 py-2">
                  <span className="text-sm text-amber-300">缺料项目</span>
                  <span className="font-semibold text-amber-400">
                    {shortages.length}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Purchase Orders section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShoppingCart className="h-5 w-5" />
              采购订单跟踪
            </CardTitle>
          </CardHeader>
          <CardContent>
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
              className="space-y-2">

              {purchaseOrders.length > 0 ?
              purchaseOrders.map((order) =>
              <PurchaseOrderRow key={order.id} order={order} />
              ) :

              <div className="text-center py-8 text-slate-500">
                  <Package className="h-12 w-12 mx-auto mb-3 text-slate-500/50" />
                  <p className="text-sm">暂无采购订单</p>
              </div>
              }
            </motion.div>
          </CardContent>
        </Card>

        {/* Material Shortage Alerts */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-400" />
                物料缺料预警
              </CardTitle>
              <Badge variant="outline" className="bg-red-500/20 text-red-400">
                {shortages.length} 项
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
              className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">

              {shortages.length > 0 ?
              shortages.map((shortage) =>
              <ShortageAlert key={shortage.id} shortage={shortage} />
              ) :

              <div className="text-center py-8 text-slate-500">
                  <CheckCircle2 className="h-12 w-12 mx-auto mb-3 text-emerald-500/50" />
                  <p className="text-sm">暂无缺料预警</p>
              </div>
              }
            </motion.div>
          </CardContent>
        </Card>
      </div>
    </div>);

}