/**
 * Finance Manager Dashboard - Main dashboard for finance department manager
 * Features: Financial overview, Budget control, Payment approval, Cost analysis, Team management
 * Core Functions: Financial team management, Budget monitoring, Financial analysis, Cash flow management
 */

import { useState, useMemo, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  Target,
  Briefcase,
  BarChart3,
  PieChart,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Building2,
  FileText,
  CreditCard,
  Receipt,
  Award,
  Activity,
  Zap,
  ChevronRight,
  Shield,
  Eye,
  ClipboardCheck,
  Calculator,
  Wallet,
  Banknote,
  TrendingDown as TrendingDownIcon,
  ArrowRight,
  Filter,
  Search,
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { costApi, invoiceApi, projectApi, purchaseApi } from "../services/api";

// Mock financial statistics
// Mock data - 已移除，使用真实API
// Mock pending payment approvals
const pendingPayments = [
  {
    id: 1,
    type: "purchase",
    orderNo: "PO-2025-0018",
    supplier: "深圳XX供应商",
    projectName: "BMS老化测试设备",
    amount: 180000,
    submitter: "陈采购",
    submitTime: "2025-01-06 10:30",
    priority: "high",
    daysPending: 0,
    dueDate: "2025-01-08",
  },
  {
    id: 2,
    type: "outsourcing",
    orderNo: "OS-2025-0012",
    supplier: "东莞精密工厂",
    projectName: "EOL功能测试设备",
    amount: 240000,
    submitter: "生产部",
    submitTime: "2025-01-06 09:15",
    priority: "high",
    daysPending: 0,
    dueDate: "2025-01-10",
  },
  {
    id: 3,
    type: "expense",
    orderNo: "EXP-2025-0045",
    category: "差旅费",
    projectName: "ICT在线测试设备",
    amount: 8500,
    submitter: "李项目经理",
    submitTime: "2025-01-05 16:45",
    priority: "medium",
    daysPending: 1,
    dueDate: "2025-01-15",
  },
  {
    id: 4,
    type: "salary",
    orderNo: "SAL-2025-0001",
    category: "工资",
    department: "生产部",
    amount: 285000,
    submitter: "人事部",
    submitTime: "2025-01-05 14:20",
    priority: "high",
    daysPending: 1,
    dueDate: "2025-01-10",
  },
  {
    id: 5,
    type: "purchase",
    orderNo: "PO-2025-0019",
    supplier: "苏州电器供应",
    projectName: "AOI视觉检测系统",
    amount: 170000,
    submitter: "褚工",
    submitTime: "2025-01-04 11:30",
    priority: "medium",
    daysPending: 2,
    dueDate: "2025-01-12",
  },
];

// Mock project cost analysis
const projectCosts = [
  {
    id: "PJ250108001",
    name: "BMS老化测试设备",
    customer: "深圳XX科技",
    budget: 850000,
    actual: 720000,
    variance: -130000,
    variancePercent: -15.3,
    status: "under_budget",
    progress: 78,
  },
  {
    id: "PJ250106002",
    name: "EOL功能测试设备",
    customer: "东莞XX电子",
    budget: 620000,
    actual: 680000,
    variance: 60000,
    variancePercent: 9.7,
    status: "over_budget",
    progress: 65,
  },
  {
    id: "PJ250103003",
    name: "ICT在线测试设备",
    customer: "惠州XX电池",
    budget: 450000,
    actual: 385000,
    variance: -65000,
    variancePercent: -14.4,
    status: "under_budget",
    progress: 45,
  },
  {
    id: "PJ250102004",
    name: "AOI视觉检测系统",
    customer: "某LED生产商",
    budget: 380000,
    actual: 420000,
    variance: 40000,
    variancePercent: 10.5,
    status: "over_budget",
    progress: 92,
  },
];

// Mock team members
// Mock data - 已移除，使用真实API
// Mock monthly trends
// Mock data - 已移除，使用真实API
// Mock cost breakdown by category
// Mock data - 已移除，使用真实API
// Mock revenue by project type
// Mock data - 已移除，使用真实API
// Mock budget execution
// Mock data - 已移除，使用真实API
const formatCurrency = (value) => {
  if (value >= 100000000) {
    return `¥${(value / 100000000).toFixed(2)}亿`;
  }
  if (value >= 10000) {
    return `¥${(value / 10000).toFixed(1)}万`;
  }
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
    minimumFractionDigits: 0,
  }).format(value);
};

const StatCard = ({ title, value, subtitle, trend, icon: Icon, color, bg }) => {
  return (
    <motion.div
      variants={fadeIn}
      className="relative overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 backdrop-blur transition-all hover:border-slate-600/80 hover:shadow-lg"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-slate-400 mb-2">{title}</p>
          <p className={cn("text-2xl font-bold mb-1", color)}>{value}</p>
          {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
          {trend !== undefined && (
            <div className="flex items-center gap-1 mt-2">
              {trend > 0 ? (
                <>
                  <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">+{trend}%</span>
                </>
              ) : trend < 0 ? (
                <>
                  <ArrowDownRight className="w-3 h-3 text-red-400" />
                  <span className="text-xs text-red-400">{trend}%</span>
                </>
              ) : null}
              {trend !== 0 && (
                <span className="text-xs text-slate-500 ml-1">vs 上月</span>
              )}
            </div>
          )}
        </div>
        <div className={cn("rounded-lg p-3 bg-opacity-20", bg)}>
          <Icon className={cn("h-6 w-6", color)} />
        </div>
      </div>
      <div className="absolute right-0 bottom-0 h-20 w-20 rounded-full bg-gradient-to-br from-purple-500/10 to-transparent blur-2xl opacity-30" />
    </motion.div>
  );
};

export default function FinanceManagerDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [financialStats, setFinancialStats] = useState({});
  const [pendingPayments, setPendingPayments] = useState([]);
  const [projectCosts, setProjectCosts] = useState([]);
  const [selectedTab, setSelectedTab] = useState("overview");
  const [timeRange, setTimeRange] = useState("month"); // month, quarter, year

  // Load financial data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Calculate date range
      const now = new Date();
      const startDate =
        timeRange === "month"
          ? new Date(now.getFullYear(), now.getMonth(), 1)
              .toISOString()
              .split("T")[0]
          : timeRange === "quarter"
            ? new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3, 1)
                .toISOString()
                .split("T")[0]
            : new Date(now.getFullYear(), 0, 1).toISOString().split("T")[0];
      const endDate = now.toISOString().split("T")[0];

      // Load project costs
      const costsResponse = await costApi.list({
        page: 1,
        page_size: 1000,
        start_date: startDate,
        end_date: endDate,
      });
      const costsData = costsResponse.data?.items || costsResponse.data || [];

      // Load invoices
      const invoicesResponse = await invoiceApi.list({
        page: 1,
        page_size: 100,
        status: "PENDING,ISSUED,PAID",
      });
      const invoicesData =
        invoicesResponse.data?.items || invoicesResponse.data || [];

      // Load projects
      const projectsResponse = await projectApi.list({
        page: 1,
        page_size: 100,
      });
      const projectsData =
        projectsResponse.data?.items || projectsResponse.data || [];

      // Load purchase orders (for pending payments)
      const purchaseOrdersResponse = await purchaseApi.orders.list({
        page: 1,
        page_size: 100,
        status: "SUBMITTED,APPROVED",
      });
      const purchaseOrdersData =
        purchaseOrdersResponse.data?.items || purchaseOrdersResponse.data || [];

      // Calculate financial statistics
      const monthlyRevenue = invoicesData
        .filter(
          (inv) =>
            inv.status === "PAID" &&
            new Date(inv.paid_date || inv.created_at).getMonth() ===
              now.getMonth(),
        )
        .reduce((sum, inv) => sum + (parseFloat(inv.amount) || 0), 0);

      const monthlyCost = costsData
        .filter(
          (cost) => new Date(cost.cost_date).getMonth() === now.getMonth(),
        )
        .reduce((sum, cost) => sum + (parseFloat(cost.amount) || 0), 0);

      const yearRevenue = invoicesData
        .filter(
          (inv) =>
            inv.status === "PAID" &&
            new Date(inv.paid_date || inv.created_at).getFullYear() ===
              now.getFullYear(),
        )
        .reduce((sum, inv) => sum + (parseFloat(inv.amount) || 0), 0);

      const yearCost = costsData
        .filter(
          (cost) =>
            new Date(cost.cost_date).getFullYear() === now.getFullYear(),
        )
        .reduce((sum, cost) => sum + (parseFloat(cost.amount) || 0), 0);

      const monthlyProfit = monthlyRevenue - monthlyCost;
      const monthlyProfitMargin =
        monthlyRevenue > 0 ? (monthlyProfit / monthlyRevenue) * 100 : 0;
      const yearProfit = yearRevenue - yearCost;
      const yearProfitMargin =
        yearRevenue > 0 ? (yearProfit / yearRevenue) * 100 : 0;

      const pendingInvoices = invoicesData.filter(
        (inv) => inv.status === "PENDING" || inv.status === "ISSUED",
      );
      const pendingInvoicesAmount = pendingInvoices.reduce(
        (sum, inv) => sum + (parseFloat(inv.amount) || 0),
        0,
      );
      const paidInvoices = invoicesData.filter((inv) => inv.status === "PAID");
      const paidInvoicesAmount = paidInvoices.reduce(
        (sum, inv) => sum + (parseFloat(inv.amount) || 0),
        0,
      );

      // Transform pending payments from purchase orders
      const transformedPayments = purchaseOrdersData
        .filter((po) => po.status === "SUBMITTED" || po.status === "APPROVED")
        .slice(0, 20)
        .map((po) => ({
          id: po.id,
          type: "purchase",
          orderNo: po.order_no || `PO-${po.id}`,
          supplier: po.supplier_name || "",
          projectName: po.project_name || "",
          amount: parseFloat(po.total_amount || po.amount || 0),
          submitter: po.created_by_name || "",
          submitTime: po.created_at || "",
          priority: po.urgency?.toLowerCase() || "medium",
          daysPending: po.created_at
            ? Math.floor(
                (now - new Date(po.created_at)) / (1000 * 60 * 60 * 24),
              )
            : 0,
          dueDate: po.expected_delivery_date || "",
        }));

      setPendingPayments(transformedPayments);

      // Transform project costs
      const transformedProjectCosts = await Promise.all(
        projectsData.slice(0, 20).map(async (project) => {
          try {
            const summaryResponse = await costApi.getProjectSummary(project.id);
            const summary = summaryResponse.data || {};
            const totalCost = parseFloat(summary.total_amount || 0);
            const budget = parseFloat(
              project.budget || project.contract_amount || 0,
            );
            const used = budget > 0 ? (totalCost / budget) * 100 : 0;

            return {
              id: project.id,
              name: project.project_name || "",
              customer: project.customer_name || "",
              budget: budget,
              actual: totalCost,
              used: used,
              variance: totalCost - budget,
              status: used > 100 ? "warning" : used > 90 ? "caution" : "good",
            };
          } catch (err) {
            return {
              id: project.id,
              name: project.project_name || "",
              customer: project.customer_name || "",
              budget: parseFloat(
                project.budget || project.contract_amount || 0,
              ),
              actual: 0,
              used: 0,
              variance: 0,
              status: "good",
            };
          }
        }),
      );

      setProjectCosts(transformedProjectCosts);

      // Update financial stats
      setFinancialStats({
        monthlyRevenue,
        monthlyTarget: 12000000,
        monthlyProgress: 12000000 > 0 ? (monthlyRevenue / 12000000) * 100 : 0,
        yearRevenue,
        yearTarget: 150000000,
        yearProgress: 150000000 > 0 ? (yearRevenue / 150000000) * 100 : 0,
        monthlyCost,
        monthlyBudget: 10000000,
        budgetUsed: 10000000 > 0 ? (monthlyCost / 10000000) * 100 : 0,
        yearCost,
        yearBudget: 120000000,
        yearBudgetUsed: 120000000 > 0 ? (yearCost / 120000000) * 100 : 0,
        monthlyProfit,
        monthlyProfitMargin,
        yearProfit,
        yearProfitMargin,
        cashFlow: monthlyRevenue - monthlyCost,
        accountsReceivable: pendingInvoicesAmount,
        overdueReceivable: 0,
        collectionRate:
          yearRevenue > 0
            ? ((yearRevenue - pendingInvoicesAmount) / yearRevenue) * 100
            : 0,
        accountsPayable: transformedPayments.reduce(
          (sum, p) => sum + p.amount,
          0,
        ),
        overduePayable: 0,
        pendingPayments: transformedPayments.length,
        pendingAmount: transformedPayments.reduce(
          (sum, p) => sum + p.amount,
          0,
        ),
        urgentPayments: transformedPayments.filter(
          (p) => p.priority === "high" || p.priority === "urgent",
        ).length,
        pendingInvoices: pendingInvoices.length,
        invoicedAmount: pendingInvoicesAmount,
        paidInvoices: paidInvoices.length,
        paidAmount: paidInvoicesAmount,
        activeProjects: projectsData.length,
        projectsOverBudget: transformedProjectCosts.filter((p) => p.used > 100)
          .length,
        totalProjectCost: transformedProjectCosts.reduce(
          (sum, p) => sum + p.actual,
          0,
        ),
        totalProjectBudget: transformedProjectCosts.reduce(
          (sum, p) => sum + p.budget,
          0,
        ),
        teamSize: 6,
        activeTeamMembers: 6,
      });
    } catch (err) {
      console.error("Failed to load financial data:", err);
      setError(err.message || "加载财务数据失败");
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="财务管理"
          subtitle="财务部经理工作台"
          icon={Calculator}
        />
        <div className="text-center py-16">
          <div className="text-slate-400">加载中...</div>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="财务管理"
        subtitle="财务部经理工作台"
        icon={Calculator}
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              财务报表
            </Button>
            <Button className="flex items-center gap-2">
              <ClipboardCheck className="w-4 h-4" />
              审批中心
            </Button>
          </motion.div>
        }
      />

      {/* Key Statistics - 6 column grid */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6"
      >
        <StatCard
          title="本月营收"
          value={formatCurrency(financialStats.monthlyRevenue)}
          subtitle={`目标: ${formatCurrency(financialStats.monthlyTarget)}`}
          trend={18.5}
          icon={DollarSign}
          color="text-amber-400"
          bg="bg-amber-500/10"
        />
        <StatCard
          title="本月成本"
          value={formatCurrency(financialStats.monthlyCost)}
          subtitle={`预算: ${formatCurrency(financialStats.monthlyBudget)}`}
          trend={-2.3}
          icon={TrendingDownIcon}
          color="text-red-400"
          bg="bg-red-500/10"
        />
        <StatCard
          title="净利润"
          value={formatCurrency(financialStats.monthlyProfit)}
          subtitle={`利润率: ${financialStats.monthlyProfitMargin}%`}
          trend={15.2}
          icon={TrendingUp}
          color="text-emerald-400"
          bg="bg-emerald-500/10"
        />
        <StatCard
          title="待审批付款"
          value={financialStats.pendingPayments}
          subtitle={`金额: ${formatCurrency(financialStats.pendingAmount)}`}
          icon={ClipboardCheck}
          color="text-red-400"
          bg="bg-red-500/10"
        />
        <StatCard
          title="应收账款"
          value={formatCurrency(financialStats.accountsReceivable)}
          subtitle={`逾期: ${formatCurrency(financialStats.overdueReceivable)}`}
          icon={CreditCard}
          color="text-blue-400"
          bg="bg-blue-500/10"
        />
        <StatCard
          title="现金流"
          value={formatCurrency(financialStats.cashFlow)}
          subtitle="可用资金"
          trend={8.5}
          icon={Wallet}
          color="text-cyan-400"
          bg="bg-cyan-500/10"
        />
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Budget & Cost Analysis */}
        <div className="lg:col-span-2 space-y-6">
          {/* Year Progress */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Activity className="h-5 w-5 text-cyan-400" />
                  年度财务目标进度
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-slate-400 mb-1">
                        年度营收目标
                      </p>
                      <p className="text-2xl font-bold text-white">
                        {formatCurrency(mockFinancialStats.yearTarget)}
                      </p>
                      <div className="mt-2">
                        <Progress
                          value={mockFinancialStats.yearProgress}
                          className="h-3 bg-slate-700/50"
                        />
                        <div className="flex items-center justify-between text-xs mt-1">
                          <span className="text-slate-400">
                            完成率: {mockFinancialStats.yearProgress.toFixed(1)}
                            %
                          </span>
                          <span className="text-emerald-400">
                            已完成:{" "}
                            {formatCurrency(mockFinancialStats.yearRevenue)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">
                        年度成本预算
                      </p>
                      <p className="text-2xl font-bold text-white">
                        {formatCurrency(mockFinancialStats.yearBudget)}
                      </p>
                      <div className="mt-2">
                        <Progress
                          value={mockFinancialStats.yearBudgetUsed}
                          className="h-3 bg-slate-700/50"
                        />
                        <div className="flex items-center justify-between text-xs mt-1">
                          <span className="text-slate-400">
                            使用率:{" "}
                            {mockFinancialStats.yearBudgetUsed.toFixed(1)}%
                          </span>
                          <span className="text-red-400">
                            已用: {formatCurrency(mockFinancialStats.yearCost)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="pt-4 border-t border-slate-700/50">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-slate-400">年度净利润</p>
                        <p className="text-2xl font-bold text-emerald-400 mt-1">
                          {formatCurrency(mockFinancialStats.yearProfit)}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          利润率: {mockFinancialStats.yearProfitMargin}%
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-slate-400">预算执行率</p>
                        <p className="text-2xl font-bold text-white mt-1">
                          {mockFinancialStats.yearBudgetUsed.toFixed(1)}%
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          {mockFinancialStats.yearBudgetUsed < 100
                            ? "良好"
                            : "超支"}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Budget Execution */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Target className="h-5 w-5 text-purple-400" />
                    预算执行情况
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs text-primary"
                  >
                    查看详情 <ChevronRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mockBudgetExecution.map((item, index) => {
                    const statusColors = {
                      good: "bg-emerald-500",
                      warning: "bg-amber-500",
                      critical: "bg-red-500",
                    };
                    return (
                      <div key={index} className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">
                            {item.category}
                          </span>
                          <div className="flex items-center gap-3">
                            <span className="text-slate-500 text-xs">
                              预算: {formatCurrency(item.budget)}
                            </span>
                            <span
                              className={cn(
                                "font-medium",
                                item.variance > 0
                                  ? "text-red-400"
                                  : "text-emerald-400",
                              )}
                            >
                              实际: {formatCurrency(item.actual)}
                            </span>
                            {item.variance !== 0 && (
                              <span
                                className={cn(
                                  "text-xs",
                                  item.variance > 0
                                    ? "text-red-400"
                                    : "text-emerald-400",
                                )}
                              >
                                {item.variance > 0 ? "+" : ""}
                                {formatCurrency(item.variance)}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Progress
                            value={item.used}
                            className={cn(
                              "flex-1 h-2",
                              item.status === "warning" && "bg-amber-500/20",
                            )}
                          />
                          <div className="flex items-center gap-1">
                            <div
                              className={cn(
                                "w-2 h-2 rounded-full",
                                statusColors[item.status],
                              )}
                            />
                            <span className="text-xs text-slate-400 w-12 text-right">
                              {item.used.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Financial Trends */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <BarChart3 className="h-5 w-5 text-cyan-400" />
                    财务趋势分析
                  </CardTitle>
                  <div className="flex gap-2">
                    <Button
                      variant={timeRange === "month" ? "default" : "ghost"}
                      size="sm"
                      className="text-xs"
                      onClick={() => setTimeRange("month")}
                    >
                      月度
                    </Button>
                    <Button
                      variant={timeRange === "quarter" ? "default" : "ghost"}
                      size="sm"
                      className="text-xs"
                      onClick={() => setTimeRange("quarter")}
                    >
                      季度
                    </Button>
                    <Button
                      variant={timeRange === "year" ? "default" : "ghost"}
                      size="sm"
                      className="text-xs"
                      onClick={() => setTimeRange("year")}
                    >
                      年度
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="revenue" className="w-full">
                  <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="revenue">营收</TabsTrigger>
                    <TabsTrigger value="cost">成本</TabsTrigger>
                    <TabsTrigger value="profit">利润</TabsTrigger>
                    <TabsTrigger value="cashflow">现金流</TabsTrigger>
                  </TabsList>
                  <TabsContent value="revenue" className="space-y-4 mt-4">
                    {mockMonthlyTrends.map((item, index) => {
                      const maxRevenue = Math.max(
                        ...mockMonthlyTrends.map((t) => t.revenue),
                      );
                      const percentage = (item.revenue / maxRevenue) * 100;
                      return (
                        <div key={index} className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-slate-400">{item.month}</span>
                            <div className="flex items-center gap-3">
                              <span className="text-white font-medium">
                                {formatCurrency(item.revenue)}
                              </span>
                              {index > 0 && (
                                <span
                                  className={cn(
                                    "text-xs",
                                    item.revenue >
                                      mockMonthlyTrends[index - 1].revenue
                                      ? "text-emerald-400"
                                      : "text-red-400",
                                  )}
                                >
                                  {item.revenue >
                                  mockMonthlyTrends[index - 1].revenue
                                    ? "↑"
                                    : "↓"}
                                  {Math.abs(
                                    ((item.revenue -
                                      mockMonthlyTrends[index - 1].revenue) /
                                      mockMonthlyTrends[index - 1].revenue) *
                                      100,
                                  ).toFixed(1)}
                                  %
                                </span>
                              )}
                            </div>
                          </div>
                          <Progress
                            value={percentage}
                            className="h-2 bg-slate-700/50"
                          />
                        </div>
                      );
                    })}
                  </TabsContent>
                  <TabsContent value="cost" className="space-y-4 mt-4">
                    {mockMonthlyTrends.map((item, index) => {
                      const maxCost = Math.max(
                        ...mockMonthlyTrends.map((t) => t.cost),
                      );
                      const percentage = (item.cost / maxCost) * 100;
                      return (
                        <div key={index} className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-slate-400">{item.month}</span>
                            <div className="flex items-center gap-3">
                              <span className="text-white font-medium">
                                {formatCurrency(item.cost)}
                              </span>
                              {index > 0 && (
                                <span
                                  className={cn(
                                    "text-xs",
                                    item.cost <
                                      mockMonthlyTrends[index - 1].cost
                                      ? "text-emerald-400"
                                      : "text-red-400",
                                  )}
                                >
                                  {item.cost < mockMonthlyTrends[index - 1].cost
                                    ? "↓"
                                    : "↑"}
                                  {Math.abs(
                                    ((item.cost -
                                      mockMonthlyTrends[index - 1].cost) /
                                      mockMonthlyTrends[index - 1].cost) *
                                      100,
                                  ).toFixed(1)}
                                  %
                                </span>
                              )}
                            </div>
                          </div>
                          <Progress
                            value={percentage}
                            className="h-2 bg-slate-700/50"
                          />
                        </div>
                      );
                    })}
                  </TabsContent>
                  <TabsContent value="profit" className="space-y-4 mt-4">
                    {mockMonthlyTrends.map((item, index) => {
                      const maxProfit = Math.max(
                        ...mockMonthlyTrends.map((t) => t.profit),
                      );
                      const percentage = (item.profit / maxProfit) * 100;
                      return (
                        <div key={index} className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-slate-400">{item.month}</span>
                            <div className="flex items-center gap-3">
                              <span className="text-emerald-400 font-medium">
                                {formatCurrency(item.profit)}
                              </span>
                              {index > 0 && (
                                <span
                                  className={cn(
                                    "text-xs",
                                    item.profit >
                                      mockMonthlyTrends[index - 1].profit
                                      ? "text-emerald-400"
                                      : "text-red-400",
                                  )}
                                >
                                  {item.profit >
                                  mockMonthlyTrends[index - 1].profit
                                    ? "↑"
                                    : "↓"}
                                  {Math.abs(
                                    ((item.profit -
                                      mockMonthlyTrends[index - 1].profit) /
                                      mockMonthlyTrends[index - 1].profit) *
                                      100,
                                  ).toFixed(1)}
                                  %
                                </span>
                              )}
                            </div>
                          </div>
                          <Progress
                            value={percentage}
                            className="h-2 bg-slate-700/50"
                          />
                        </div>
                      );
                    })}
                  </TabsContent>
                  <TabsContent value="cashflow" className="space-y-4 mt-4">
                    {mockMonthlyTrends.map((item, index) => {
                      const maxCashFlow = Math.max(
                        ...mockMonthlyTrends.map((t) => t.cashFlow),
                      );
                      const percentage = (item.cashFlow / maxCashFlow) * 100;
                      return (
                        <div key={index} className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-slate-400">{item.month}</span>
                            <div className="flex items-center gap-3">
                              <span className="text-cyan-400 font-medium">
                                {formatCurrency(item.cashFlow)}
                              </span>
                              {index > 0 && (
                                <span
                                  className={cn(
                                    "text-xs",
                                    item.cashFlow >
                                      mockMonthlyTrends[index - 1].cashFlow
                                      ? "text-emerald-400"
                                      : "text-red-400",
                                  )}
                                >
                                  {item.cashFlow >
                                  mockMonthlyTrends[index - 1].cashFlow
                                    ? "↑"
                                    : "↓"}
                                  {Math.abs(
                                    ((item.cashFlow -
                                      mockMonthlyTrends[index - 1].cashFlow) /
                                      mockMonthlyTrends[index - 1].cashFlow) *
                                      100,
                                  ).toFixed(1)}
                                  %
                                </span>
                              )}
                            </div>
                          </div>
                          <Progress
                            value={percentage}
                            className="h-2 bg-slate-700/50"
                          />
                        </div>
                      );
                    })}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </motion.div>

          {/* Project Cost Analysis */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Briefcase className="h-5 w-5 text-blue-400" />
                    项目成本分析
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs text-primary"
                  >
                    查看全部 <ChevronRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {projectCosts.map((project) => {
                    const statusColors = {
                      under_budget: "bg-emerald-500",
                      over_budget: "bg-red-500",
                    };
                    return (
                      <div
                        key={project.id}
                        className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-white">
                                {project.name}
                              </span>
                              <div
                                className={cn(
                                  "w-2 h-2 rounded-full",
                                  statusColors[project.status],
                                )}
                              />
                            </div>
                            <div className="text-xs text-slate-400">
                              {project.customer} · {project.id}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-bold text-white">
                              {formatCurrency(project.actual)}
                            </div>
                            <div className="text-xs text-slate-400">
                              预算: {formatCurrency(project.budget)}
                            </div>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-400">成本差异</span>
                            <div className="flex items-center gap-2">
                              <span
                                className={cn(
                                  "font-medium",
                                  project.variance > 0
                                    ? "text-red-400"
                                    : "text-emerald-400",
                                )}
                              >
                                {project.variance > 0 ? "+" : ""}
                                {formatCurrency(project.variance)}
                              </span>
                              <span
                                className={cn(
                                  project.variance > 0
                                    ? "text-red-400"
                                    : "text-emerald-400",
                                )}
                              >
                                ({project.variancePercent > 0 ? "+" : ""}
                                {project.variancePercent.toFixed(1)}%)
                              </span>
                            </div>
                          </div>
                          <Progress
                            value={project.progress}
                            className="h-1.5 bg-slate-700/50"
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Right Column - Pending Approvals & Team Status */}
        <div className="space-y-6">
          {/* Pending Payment Approvals */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <ClipboardCheck className="h-5 w-5 text-amber-400" />
                    待审批付款
                  </CardTitle>
                  <Badge
                    variant="outline"
                    className="bg-amber-500/20 text-amber-400 border-amber-500/30"
                  >
                    {pendingPayments.length}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {pendingPayments.map((item) => {
                  const typeLabels = {
                    purchase: "采购付款",
                    outsourcing: "外协付款",
                    expense: "费用报销",
                    salary: "工资发放",
                  };
                  const typeColors = {
                    purchase: "bg-blue-500/20 text-blue-400 border-blue-500/30",
                    outsourcing:
                      "bg-purple-500/20 text-purple-400 border-purple-500/30",
                    expense:
                      "bg-amber-500/20 text-amber-400 border-amber-500/30",
                    salary: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
                  };
                  return (
                    <div
                      key={item.id}
                      className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge
                              variant="outline"
                              className={cn("text-xs", typeColors[item.type])}
                            >
                              {typeLabels[item.type]}
                            </Badge>
                            {item.priority === "high" && (
                              <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                                紧急
                              </Badge>
                            )}
                          </div>
                          <p className="font-medium text-white text-sm">
                            {item.orderNo}
                          </p>
                          <p className="text-xs text-slate-400 mt-1">
                            {item.projectName ||
                              item.category ||
                              item.department}
                          </p>
                          <p className="text-xs text-slate-500 mt-1">
                            {item.supplier || item.submitter} ·{" "}
                            {item.submitTime.split(" ")[1]}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between text-xs mt-2">
                        <span className="text-slate-400">
                          {item.daysPending > 0
                            ? `待审批${item.daysPending}天`
                            : "今日提交"}
                        </span>
                        <span className="font-medium text-amber-400">
                          {formatCurrency(item.amount)}
                        </span>
                      </div>
                    </div>
                  );
                })}
                <Button variant="outline" className="w-full mt-3">
                  查看全部审批
                </Button>
              </CardContent>
            </Card>
          </motion.div>

          {/* Cost Breakdown */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <PieChart className="h-5 w-5 text-purple-400" />
                  成本构成分析
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {mockCostBreakdown.map((item, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div
                          className={cn("w-3 h-3 rounded-full", item.color)}
                        />
                        <span className="text-slate-400">{item.category}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-white font-medium">
                          {formatCurrency(item.amount)}
                        </span>
                        <span className="text-slate-500 text-xs">
                          {item.percentage}%
                        </span>
                      </div>
                    </div>
                    <Progress
                      value={item.percentage}
                      className="h-2 bg-slate-700/50"
                    />
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>

          {/* Financial Health */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Activity className="h-5 w-5 text-blue-400" />
                  财务健康度
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-slate-400">回款率</span>
                      <span className="text-emerald-400 font-medium">
                        {mockFinancialStats.collectionRate}%
                      </span>
                    </div>
                    <Progress
                      value={mockFinancialStats.collectionRate}
                      className="h-2 bg-slate-700/50"
                    />
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-slate-400">预算执行率</span>
                      <span className="text-white font-medium">
                        {mockFinancialStats.yearBudgetUsed.toFixed(1)}%
                      </span>
                    </div>
                    <Progress
                      value={mockFinancialStats.yearBudgetUsed}
                      className="h-2 bg-slate-700/50"
                    />
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-slate-400">利润率</span>
                      <span className="text-emerald-400 font-medium">
                        {mockFinancialStats.yearProfitMargin}%
                      </span>
                    </div>
                    <Progress
                      value={mockFinancialStats.yearProfitMargin}
                      className="h-2 bg-slate-700/50"
                    />
                  </div>
                </div>
                <div className="pt-4 border-t border-slate-700/50 grid grid-cols-2 gap-3">
                  <div className="text-center p-3 bg-slate-800/40 rounded-lg">
                    <div className="text-lg font-bold text-emerald-400">
                      {formatCurrency(mockFinancialStats.cashFlow)}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      可用现金流
                    </div>
                  </div>
                  <div className="text-center p-3 bg-slate-800/40 rounded-lg">
                    <div className="text-lg font-bold text-red-400">
                      {mockFinancialStats.projectsOverBudget}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      超预算项目
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Team Status */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Users className="h-5 w-5 text-blue-400" />
                    财务团队
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs text-primary"
                  >
                    管理 <ChevronRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {mockTeamMembers.map((member) => {
                  const performanceColors = {
                    excellent: "text-emerald-400",
                    good: "text-blue-400",
                    warning: "text-amber-400",
                  };
                  return (
                    <div
                      key={member.id}
                      className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-white text-sm">
                              {member.name}
                            </span>
                            <Badge
                              variant="outline"
                              className="text-xs bg-slate-700/40"
                            >
                              {member.role}
                            </Badge>
                          </div>
                          <div className="text-xs text-slate-400 mt-1">
                            本月任务: {member.monthlyTasks}
                          </div>
                        </div>
                        <div className="text-right">
                          <div
                            className={cn(
                              "text-sm font-bold",
                              performanceColors[member.performance],
                            )}
                          >
                            {member.completionRate}%
                          </div>
                          <div className="text-xs text-slate-400">完成率</div>
                        </div>
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-400">准确率</span>
                          <span className="text-white">{member.accuracy}%</span>
                        </div>
                        <Progress
                          value={member.accuracy}
                          className="h-1.5 bg-slate-700/50"
                        />
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}
