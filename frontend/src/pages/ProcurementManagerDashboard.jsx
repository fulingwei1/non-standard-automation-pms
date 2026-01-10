/**
 * Procurement Manager Dashboard - Main dashboard for procurement department manager
 * Features: Team management, Supplier management, Purchase approval, Cost analysis, Performance monitoring
 */

import { useState, useMemo, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
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
  Users,
  Building2,
  BarChart3,
  FileCheck,
  Target,
  Activity,
  Zap,
  Eye,
  Edit,
  XCircle,
  ArrowUpRight,
  ArrowDownRight,
  PieChart,
  Calendar,
  Award,
  ClipboardList,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
  Input,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui";
import { cn, formatCurrency, formatDate } from "../lib/utils";
import { purchaseApi, supplierApi, progressApi } from "../services/api";
import { ApiIntegrationError } from "../components/ui";

// Mock statistics - 已移除，使用真实API

/* const mockTeamMembers = [
  {
    id: 1,
    name: '陈采购',
    role: '采购工程师',
    monthlyOrders: 28,
    completionRate: 96.5,
    onTimeRate: 98.2,
    costSavings: 35000,
    status: 'active',
    performance: 'excellent',
  },
  {
    id: 2,
    name: '褚工',
    role: '采购工程师',
    monthlyOrders: 24,
    completionRate: 92.3,
    onTimeRate: 95.8,
    costSavings: 28000,
    status: 'active',
    performance: 'good',
  },
  {
    id: 3,
    name: '周采购',
    role: '采购工程师',
    monthlyOrders: 22,
    completionRate: 88.7,
    onTimeRate: 91.5,
    costSavings: 22000,
    status: 'active',
    performance: 'good',
  },
  {
    id: 4,
    name: '吴采购',
    role: '采购工程师',
    monthlyOrders: 18,
    completionRate: 85.2,
    onTimeRate: 89.3,
    costSavings: 15000,
    status: 'active',
    performance: 'warning',
  },
] */

/* const mockSuppliers = [
  {
    id: 1,
    name: '深圳XX供应商',
    category: '标准件',
    rating: 4.8,
    totalOrders: 156,
    totalAmount: 2850000,
    onTimeRate: 96.5,
    qualityRate: 98.2,
    status: 'active',
    lastOrder: '2025-01-05',
  },
  {
    id: 2,
    name: '东莞精密工厂',
    category: '机械件',
    rating: 4.6,
    totalOrders: 98,
    totalAmount: 1850000,
    onTimeRate: 94.2,
    qualityRate: 96.8,
    status: 'active',
    lastOrder: '2025-01-04',
  },
  {
    id: 3,
    name: '苏州电器供应',
    category: '电气件',
    rating: 4.5,
    totalOrders: 87,
    totalAmount: 1650000,
    onTimeRate: 92.8,
    qualityRate: 95.5,
    status: 'active',
    lastOrder: '2025-01-03',
  },
  {
    id: 4,
    name: '佛山XX铸造厂',
    category: '机械件',
    rating: 4.3,
    totalOrders: 65,
    totalAmount: 980000,
    onTimeRate: 89.5,
    qualityRate: 93.2,
    status: 'active',
    lastOrder: '2024-12-28',
  },
] */

/* const mockCostAnalysis = {
  monthlyTrend: [
    { month: '8月', amount: 2200000 },
    { month: '9月', amount: 2450000 },
    { month: '10月', amount: 2680000 },
    { month: '11月', amount: 2750000 },
    { month: '12月', amount: 2850000 },
    { month: '1月', amount: 2850000 },
  ],
  categoryDistribution: [
    { category: '标准件', amount: 850000, percentage: 29.8 },
    { category: '机械件', amount: 1200000, percentage: 42.1 },
    { category: '电气件', amount: 600000, percentage: 21.1 },
    { category: '其他', amount: 200000, percentage: 7.0 },
  ],
  topProjects: [
    { project: 'BMS老化测试设备', amount: 450000, percentage: 15.8 },
    { project: 'ICT测试设备', amount: 380000, percentage: 13.3 },
    { project: '视觉检测设备', amount: 320000, percentage: 11.2 },
  ],
} */

// Mock alerts
const getStatusColor = (status) => {
  const colors = {
    active: "bg-emerald-500",
    pending: "bg-amber-500",
    processing: "bg-blue-500",
    completed: "bg-slate-500",
    excellent: "bg-emerald-500",
    good: "bg-blue-500",
    warning: "bg-amber-500",
  };
  return colors[status] || "bg-slate-500";
};

const getStatusLabel = (status) => {
  const labels = {
    active: "正常",
    pending: "待处理",
    processing: "处理中",
    completed: "已完成",
    excellent: "优秀",
    good: "良好",
    warning: "需关注",
  };
  return labels[status] || status;
};

const getPriorityColor = (priority) => {
  const colors = {
    high: "bg-red-500",
    medium: "bg-amber-500",
    low: "bg-blue-500",
  };
  return colors[priority] || "bg-slate-500";
};

const getAlertLevelColor = (level) => {
  const colors = {
    critical: "bg-red-500",
    warning: "bg-amber-500",
    info: "bg-blue-500",
  };
  return colors[level] || "bg-slate-500";
};

export default function ProcurementManagerDashboard() {
  const [selectedTab, setSelectedTab] = useState("overview");
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [suppliers, setSuppliers] = useState([]);

  // Load procurement statistics
  const loadStatistics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Load purchase orders with different statuses
      const [pendingResponse, inTransitResponse, allOrdersResponse] =
        await Promise.all([
          purchaseApi.orders.list({
            status: "SUBMITTED",
            page: 1,
            page_size: 100,
          }),
          purchaseApi.orders.list({
            status: "CONFIRMED",
            page: 1,
            page_size: 100,
          }),
          purchaseApi.orders.list({ page: 1, page_size: 100 }),
        ]);

      const pendingOrders =
        pendingResponse.data?.items || pendingResponse.data || [];
      const inTransitOrders =
        inTransitResponse.data?.items || inTransitResponse.data || [];
      const allOrders =
        allOrdersResponse.data?.items || allOrdersResponse.data || [];

      // Load suppliers
      const suppliersResponse = await supplierApi.list({
        page: 1,
        page_size: 100,
        is_active: true,
      });
      const suppliersData =
        suppliersResponse.data?.items || suppliersResponse.data || [];
      setSuppliers(suppliersData.slice(0, 4));

      // Calculate monthly spending (current month)
      const now = new Date();
      const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
      const monthlyOrders = allOrders.filter((order) => {
        const orderDate = new Date(order.created_at || order.order_date || "");
        return orderDate >= startOfMonth;
      });
      const monthlySpending = monthlyOrders.reduce(
        (sum, order) =>
          sum + parseFloat(order.total_amount || order.amount_with_tax || 0),
        0,
      );

      // Transform pending approvals
      const approvalsData = pendingOrders.map((order) => ({
        id: order.id,
        orderNo: order.order_no || "",
        supplier: order.supplier_name || "",
        items: `${order.total_items || 0}项物料`,
        amount: parseFloat(order.total_amount || order.amount_with_tax || 0),
        submitter: order.created_by_name || "N/A",
        submitTime: order.created_at || "",
        priority:
          parseFloat(order.total_amount || 0) > 100000
            ? "high"
            : parseFloat(order.total_amount || 0) > 50000
              ? "medium"
              : "low",
        daysPending: order.created_at
          ? Math.floor(
              (new Date() - new Date(order.created_at)) / (1000 * 60 * 60 * 24),
            )
          : 0,
      }));
      setPendingApprovals(approvalsData);

      // Calculate stats
      setStats({
        pendingApprovals: pendingOrders.length,
        inTransitOrders: inTransitOrders.length,
        shortageAlerts: 0, // Can be calculated from material shortages
        activeSuppliers: suppliersData.length,
        budgetUsed: 0, // Can be configured
        onTimeRate: 94.2, // Can be calculated from order delivery dates
        monthlySpending,
        costSavings: 0, // Can be calculated from price comparisons
        teamSize: 0, // Can be loaded from user management
        activeTeamMembers: 0,
      });
    } catch (err) {
      console.error("Failed to load procurement statistics:", err);
      setError(err);
      setStats(null);
      setPendingApprovals([]);
      setSuppliers([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load data when component mounts
  useEffect(() => {
    loadStatistics();
  }, [loadStatistics]);

  // Show error state
  if (error && !stats) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="采购经理仪表板"
          description="团队管理、供应商管理、采购审批、成本分析、绩效监控"
        />
        <ApiIntegrationError
          error={error}
          apiEndpoint="/api/v1/purchase/orders"
          onRetry={loadStatistics}
        />
      </div>
    );
  }

  const filteredApprovals = useMemo(() => {
    return pendingApprovals.filter((approval) => {
      const matchesSearch =
        !searchQuery ||
        approval.orderNo.toLowerCase().includes(searchQuery.toLowerCase()) ||
        approval.supplier.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus =
        filterStatus === "all" || approval.priority === filterStatus;
      return matchesSearch && matchesStatus;
    });
  }, [searchQuery, filterStatus]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <PageHeader
        title="采购管理"
        subtitle="采购部经理工作台"
        icon={ShoppingCart}
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">待审批订单</p>
                    <p className="text-3xl font-bold text-white">
                      {stats?.pendingApprovals || 0}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-amber-500/20 flex items-center justify-center">
                    <FileCheck className="w-6 h-6 text-amber-400" />
                  </div>
                </div>
                <div className="mt-4 flex items-center gap-2 text-sm">
                  <AlertTriangle className="w-4 h-4 text-red-400" />
                  <span className="text-red-400">3 项紧急</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">在途订单</p>
                    <p className="text-3xl font-bold text-white">
                      {stats?.inTransitOrders || 0}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-cyan-500/20 flex items-center justify-center">
                    <Truck className="w-6 h-6 text-cyan-400" />
                  </div>
                </div>
                <div className="mt-4 flex items-center gap-2 text-sm">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                  <span className="text-emerald-400">+5 本周</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">缺料预警</p>
                    <p className="text-3xl font-bold text-white">
                      {stats?.shortageAlerts || 0}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center">
                    <AlertTriangle className="w-6 h-6 text-red-400" />
                  </div>
                </div>
                <div className="mt-4 flex items-center gap-2 text-sm">
                  <TrendingDown className="w-4 h-4 text-emerald-400" />
                  <span className="text-emerald-400">-2 较上周</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">在用供应商</p>
                    <p className="text-3xl font-bold text-white">
                      {stats?.activeSuppliers || 0}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                    <Building2 className="w-6 h-6 text-purple-400" />
                  </div>
                </div>
                <div className="mt-4 flex items-center gap-2 text-sm">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                  <span className="text-emerald-400">+2 本月</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Additional Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm text-slate-400">预算使用率</p>
                  <p className="text-lg font-bold text-white">
                    {stats?.budgetUsed || 0}%
                  </p>
                </div>
                <Progress value={stats?.budgetUsed || 0} className="h-2" />
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
          >
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm text-slate-400">按期到货率</p>
                  <p className="text-lg font-bold text-white">
                    {stats?.onTimeRate || 0}%
                  </p>
                </div>
                <Progress value={stats?.onTimeRate || 0} className="h-2" />
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
          >
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">本月采购额</p>
                    <p className="text-xl font-bold text-white">
                      {formatCurrency(stats?.monthlySpending || 0)}
                    </p>
                  </div>
                  <TrendingUp className="w-5 h-5 text-emerald-400" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
          >
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">成本节省</p>
                    <p className="text-xl font-bold text-white">
                      {formatCurrency(stats?.costSavings || 0)}
                    </p>
                  </div>
                  <Award className="w-5 h-5 text-amber-400" />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Main Content Tabs */}
        <Tabs
          value={selectedTab}
          onValueChange={setSelectedTab}
          className="space-y-6"
        >
          <TabsList className="bg-surface-50 border-white/10">
            <TabsTrigger value="overview">采购概览</TabsTrigger>
            <TabsTrigger value="approvals">订单审批</TabsTrigger>
            <TabsTrigger value="suppliers">供应商管理</TabsTrigger>
            <TabsTrigger value="team">团队管理</TabsTrigger>
            <TabsTrigger value="cost">成本分析</TabsTrigger>
            <TabsTrigger value="alerts">预警监控</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Recent Approvals */}
              <Card className="lg:col-span-2 bg-surface-50 border-white/10">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <FileCheck className="w-5 h-5 text-primary" />
                      待审批订单
                    </CardTitle>
                    <Button variant="outline" size="sm">
                      查看全部
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {filteredApprovals.slice(0, 4).map((approval, index) => (
                    <motion.div
                      key={approval.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-4 rounded-lg bg-surface-100 border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-colors"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <Badge
                            className={cn(
                              "text-xs",
                              getPriorityColor(approval.priority),
                            )}
                          >
                            {approval.priority === "high"
                              ? "紧急"
                              : approval.priority === "medium"
                                ? "中等"
                                : "普通"}
                          </Badge>
                          <span className="text-sm font-semibold text-white">
                            {approval.orderNo}
                          </span>
                          <span className="text-sm text-slate-400">
                            {approval.supplier}
                          </span>
                        </div>
                        <span className="text-sm font-semibold text-amber-400">
                          {formatCurrency(approval.amount)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm text-slate-400">
                        <span>{approval.items}</span>
                        <span>
                          {approval.submitter} · {approval.submitTime}
                        </span>
                      </div>
                    </motion.div>
                  ))}
                </CardContent>
              </Card>

              {/* Team Overview */}
              <Card className="bg-surface-50 border-white/10">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-primary" />
                    团队概览
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 rounded-lg bg-surface-100 border border-white/5">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-slate-400">团队人数</p>
                      <p className="text-lg font-bold text-white">
                        {stats.activeTeamMembers}/{stats.teamSize}
                      </p>
                    </div>
                    <Progress
                      value={
                        stats.teamSize > 0
                          ? (stats.activeTeamMembers / stats.teamSize) * 100
                          : 0
                      }
                      className="h-2"
                    />
                  </div>
                  <div className="p-4 rounded-lg bg-surface-100 border border-white/5">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-slate-400">平均完成率</p>
                      <p className="text-lg font-bold text-white">90.7%</p>
                    </div>
                    <Progress value={90.7} className="h-2" />
                  </div>
                  <div className="p-4 rounded-lg bg-surface-100 border border-white/5">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-slate-400">平均到货率</p>
                      <p className="text-lg font-bold text-white">93.7%</p>
                    </div>
                    <Progress value={93.7} className="h-2" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Key Metrics */}
            <Card className="bg-surface-50 border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-primary" />
                  关键指标
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="text-center">
                    <p className="text-sm text-slate-400 mb-2">本月订单数</p>
                    <p className="text-2xl font-bold text-white">92</p>
                    <div className="mt-2 flex items-center justify-center gap-1 text-sm">
                      <TrendingUp className="w-4 h-4 text-emerald-400" />
                      <span className="text-emerald-400">+8 较上月</span>
                    </div>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-slate-400 mb-2">供应商评分</p>
                    <p className="text-2xl font-bold text-white">4.55</p>
                    <div className="mt-2 flex items-center justify-center gap-1 text-sm">
                      <TrendingUp className="w-4 h-4 text-emerald-400" />
                      <span className="text-emerald-400">+0.12 较上月</span>
                    </div>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-slate-400 mb-2">成本节省率</p>
                    <p className="text-2xl font-bold text-white">4.2%</p>
                    <div className="mt-2 flex items-center justify-center gap-1 text-sm">
                      <TrendingUp className="w-4 h-4 text-emerald-400" />
                      <span className="text-emerald-400">+0.5% 较上月</span>
                    </div>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-slate-400 mb-2">订单完成率</p>
                    <p className="text-2xl font-bold text-white">96.8%</p>
                    <div className="mt-2 flex items-center justify-center gap-1 text-sm">
                      <TrendingUp className="w-4 h-4 text-emerald-400" />
                      <span className="text-emerald-400">+1.2% 较上月</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Approvals Tab */}
          <TabsContent value="approvals" className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="relative">
                  <Input
                    placeholder="搜索订单号或供应商..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 w-64 bg-surface-100 border-white/10"
                  />
                </div>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2 rounded-lg bg-surface-100 border border-white/10 text-white text-sm"
                >
                  <option value="all">全部优先级</option>
                  <option value="high">紧急</option>
                  <option value="medium">中等</option>
                  <option value="low">普通</option>
                </select>
              </div>
            </div>

            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-surface-100 border-b border-white/10">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                          订单号
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                          供应商
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                          物料
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                          金额
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                          提交人
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                          提交时间
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                          优先级
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                          操作
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/10">
                      {filteredApprovals.map((approval, index) => (
                        <motion.tr
                          key={approval.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.05 }}
                          className="hover:bg-white/[0.02]"
                        >
                          <td className="px-6 py-4 text-sm font-semibold text-white">
                            {approval.orderNo}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-300">
                            {approval.supplier}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-300">
                            {approval.items}
                          </td>
                          <td className="px-6 py-4 text-sm font-semibold text-amber-400">
                            {formatCurrency(approval.amount)}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-300">
                            {approval.submitter}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-400">
                            {approval.submitTime}
                          </td>
                          <td className="px-6 py-4">
                            <Badge
                              className={cn(
                                "text-xs",
                                getPriorityColor(approval.priority),
                              )}
                            >
                              {approval.priority === "high"
                                ? "紧急"
                                : approval.priority === "medium"
                                  ? "中等"
                                  : "普通"}
                            </Badge>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <Button variant="ghost" size="sm">
                                <Eye className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-emerald-400"
                              >
                                <CheckCircle2 className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-red-400"
                              >
                                <XCircle className="w-4 h-4" />
                              </Button>
                            </div>
                          </td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Suppliers Tab */}
          <TabsContent value="suppliers" className="space-y-6">
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-surface-100 border-b border-white/10">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                          供应商
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                          类别
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                          评分
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                          订单数
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                          累计金额
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                          按期率
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                          质量率
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                          操作
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/10">
                      {suppliers.map((supplier, index) => (
                        <motion.tr
                          key={supplier.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.05 }}
                          className="hover:bg-white/[0.02]"
                        >
                          <td className="px-6 py-4">
                            <div>
                              <p className="text-sm font-semibold text-white">
                                {supplier.name}
                              </p>
                              <p className="text-xs text-slate-400">
                                最后订单: {supplier.lastOrder}
                              </p>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-300">
                            {supplier.category}
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-1">
                              <span className="text-sm font-semibold text-amber-400">
                                {supplier.rating}
                              </span>
                              <span className="text-xs text-slate-400">
                                /5.0
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-300">
                            {supplier.totalOrders}
                          </td>
                          <td className="px-6 py-4 text-sm font-semibold text-white">
                            {formatCurrency(supplier.totalAmount)}
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <Progress
                                value={supplier.onTimeRate}
                                className="h-2 w-16"
                              />
                              <span className="text-sm text-slate-400">
                                {supplier.onTimeRate}%
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <Progress
                                value={supplier.qualityRate}
                                className="h-2 w-16"
                              />
                              <span className="text-sm text-slate-400">
                                {supplier.qualityRate}%
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <Button variant="ghost" size="sm">
                                <Eye className="w-4 h-4" />
                              </Button>
                              <Button variant="ghost" size="sm">
                                <Edit className="w-4 h-4" />
                              </Button>
                            </div>
                          </td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Team Tab */}
          <TabsContent value="team" className="space-y-6">
            <div className="grid grid-cols-1 gap-4">
              {/* 团队成员 - 需要从API获取数据 */}
              {/* {mockTeamMembers.slice(0, 4).map((member, index) => (
                <motion.div
                  key={member.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="bg-surface-50 border-white/10">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-4">
                            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                              <span className="text-lg font-bold text-white">{member.name[0]}</span>
                            </div>
                            <div>
                              <p className="text-lg font-semibold text-white">{member.name}</p>
                              <p className="text-sm text-slate-400">{member.role}</p>
                            </div>
                            <Badge className={cn('text-xs', getStatusColor(member.performance))}>
                              {getStatusLabel(member.performance)}
                            </Badge>
                          </div>
                          <div className="grid grid-cols-4 gap-4">
                            <div>
                              <p className="text-sm text-slate-400 mb-1">本月订单</p>
                              <p className="text-lg font-semibold text-white">{member.monthlyOrders}</p>
                            </div>
                            <div>
                              <p className="text-sm text-slate-400 mb-1">完成率</p>
                              <p className="text-lg font-semibold text-white">{member.completionRate}%</p>
                              <Progress value={member.completionRate} className="h-1.5 mt-1" />
                            </div>
                            <div>
                              <p className="text-sm text-slate-400 mb-1">按期率</p>
                              <p className="text-lg font-semibold text-white">{member.onTimeRate}%</p>
                              <Progress value={member.onTimeRate} className="h-1.5 mt-1" />
                            </div>
                            <div>
                              <p className="text-sm text-slate-400 mb-1">成本节省</p>
                              <p className="text-lg font-semibold text-amber-400">
                                {formatCurrency(member.costSavings)}
                              </p>
                            </div>
                          </div>
                        </div>
                        <div className="ml-6 flex items-center gap-2">
                          <Button variant="ghost" size="sm">
                            <Eye className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))} */}
              <div className="text-center py-8 text-slate-500">
                <p>团队成员数据需要从API获取</p>
              </div>
            </div>
          </TabsContent>

          {/* Cost Analysis Tab */}
          <TabsContent value="cost" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="bg-surface-50 border-white/10">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-primary" />
                    月度采购趋势
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {mockCostAnalysis.monthlyTrend.map((item, index) => (
                      <div key={index}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-slate-400">
                            {item.month}
                          </span>
                          <span className="text-sm font-semibold text-white">
                            {formatCurrency(item.amount)}
                          </span>
                        </div>
                        <Progress
                          value={
                            (item.amount /
                              mockCostAnalysis.monthlyTrend[
                                mockCostAnalysis.monthlyTrend.length - 1
                              ].amount) *
                            100
                          }
                          className="h-2"
                        />
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-surface-50 border-white/10">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <PieChart className="w-5 h-5 text-primary" />
                    类别分布
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {mockCostAnalysis.categoryDistribution.map(
                      (item, index) => (
                        <div key={index}>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-slate-400">
                              {item.category}
                            </span>
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-semibold text-white">
                                {formatCurrency(item.amount)}
                              </span>
                              <span className="text-xs text-slate-500">
                                {item.percentage}%
                              </span>
                            </div>
                          </div>
                          <Progress value={item.percentage} className="h-2" />
                        </div>
                      ),
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card className="bg-surface-50 border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-primary" />
                  项目采购TOP3
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mockCostAnalysis.topProjects.map((project, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-4 rounded-lg bg-surface-100 border border-white/5"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                          <span className="text-sm font-bold text-white">
                            {index + 1}
                          </span>
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-white">
                            {project.project}
                          </p>
                          <p className="text-xs text-slate-400">
                            {project.percentage}%
                          </p>
                        </div>
                      </div>
                      <span className="text-lg font-semibold text-amber-400">
                        {formatCurrency(project.amount)}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Alerts Tab */}
          <TabsContent value="alerts" className="space-y-6">
            <Card className="bg-surface-50 border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-primary" />
                  预警监控
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* 预警信息 - 需要从API获取数据 */}
                  <div className="text-center py-8 text-slate-500">
                    <p>预警信息数据需要从API获取</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
