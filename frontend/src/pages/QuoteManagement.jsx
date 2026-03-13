/**
 * Quote Management Page - Refactored Version
 * 报价管理页面 - 重构版本
 * Features: Quote list, creation, version management, approval
 */

import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { DollarSign, PieChart, TrendingDown, TrendingUp, FileText, BarChart3 } from "lucide-react";
import { PageHeader } from "../components/layout";
import { Button } from "../components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "../components/ui/select";
import { formatCurrency, formatPercent } from "../lib/utils";
import { handleApiError } from "../utils/apiErrorHandler";

// Import refactored components
import {
  QuoteStatsOverview,
  QuoteListManager,
  DEFAULT_QUOTE_STATS,
  MarginAnalysis
} from "../components/quote";

// Import services
import {
  quoteApi,
  opportunityApi,
  customerApi,
  purchaseApi } from
"../services/api";

// Import utilities
import { fadeIn, staggerContainer } from "../lib/animations";

const DEFAULT_COST_INSIGHTS = {
  totalCost: 1280000,
  orderCount: 18,
  averageOrderCost: 71000,
  costSavings: 93000,
  savingsRate: 7.6,
  categories: [
    { name: "核心材料", amount: 520000 },
    { name: "外协加工", amount: 280000 },
    { name: "系统集成", amount: 210000 },
    { name: "安装调试", amount: 135000 }
  ],
  suppliers: [
    { name: "华东自动化", amount: 310000 },
    { name: "苏南精工", amount: 265000 },
    { name: "易联智采", amount: 188000 },
    { name: "鸿泰机电", amount: 142000 }
  ],
  trend: [
    { month: "2024-10", amount: 410000, orders: 6 },
    { month: "2024-11", amount: 368000, orders: 5 },
    { month: "2024-12", amount: 295000, orders: 4 },
    { month: "2025-01", amount: 210000, orders: 3 }
  ]
};

const EMPTY_COST_INSIGHTS = {
  totalCost: 0,
  orderCount: 0,
  averageOrderCost: 0,
  costSavings: 0,
  savingsRate: 0,
  categories: [],
  suppliers: [],
  trend: []
};

const COST_RANGE_LABELS = {
  month: "本月",
  quarter: "本季度",
  year: "本年度"
};

export default function QuoteManagement({ embedded = false } = {}) {
  const navigate = useNavigate();

  // 状态管理
  const [quotes, setQuotes] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [selectedQuotes, setSelectedQuotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedQuote, setSelectedQuote] = useState(null);

  // 统计数据
  const [stats, setStats] = useState(DEFAULT_QUOTE_STATS);

  // 视图和筛选
  const [viewMode, setViewMode] = useState("list");
  const [searchTerm, setSearchTerm] = useState("");
  const [filters, setFilters] = useState({
    status: "all",
    type: "all",
    priority: "all",
    customer_id: "all",
    opportunity_id: "all"
  });
  const [sortBy, setSortBy] = useState("created_desc");
  const [timeRange, setTimeRange] = useState("month");
  const [costTimeRange, setCostTimeRange] = useState("month");
  const [costInsights, setCostInsights] = useState(DEFAULT_COST_INSIGHTS);
  const [costLoading, setCostLoading] = useState(false);

  // 模拟报价数据（API失败时使用）
  const MOCK_QUOTES = [
    { id: 1, title: "宁德时代FCT测试线", quote_code: "QT-202603-001", status: "APPROVED", type: "PROJECT", priority: "HIGH", customer_id: 1, customer_name: "宁德时代", valid_until: "2026-04-15", created_at: "2026-03-01", version: { version_no: "V2", total_price: 3500000, cost_total: 2275000, gross_margin: 35 } },
    { id: 2, title: "比亚迪EOL检测设备", quote_code: "QT-202603-002", status: "SENT", type: "STANDARD", priority: "MEDIUM", customer_id: 2, customer_name: "比亚迪", valid_until: "2026-04-20", created_at: "2026-03-05", version: { version_no: "V1", total_price: 2800000, cost_total: 1820000, gross_margin: 35 } },
    { id: 3, title: "中创新航ICT测试系统", quote_code: "QT-202603-003", status: "DRAFT", type: "CUSTOM", priority: "LOW", customer_id: 3, customer_name: "中创新航", valid_until: "2026-05-01", created_at: "2026-03-08", version: { version_no: "V1", total_price: 1500000, cost_total: 975000, gross_margin: 35 } },
    { id: 4, title: "亿纬锂能烧录设备", quote_code: "QT-202602-015", status: "IN_REVIEW", type: "STANDARD", priority: "HIGH", customer_id: 4, customer_name: "亿纬锂能", valid_until: "2026-03-25", created_at: "2026-02-20", version: { version_no: "V3", total_price: 1800000, cost_total: 1170000, gross_margin: 35 } },
    { id: 5, title: "国轩高科Pack线测试", quote_code: "QT-202602-012", status: "ACCEPTED", type: "PROJECT", priority: "URGENT", customer_id: 5, customer_name: "国轩高科", valid_until: "2026-04-10", created_at: "2026-02-15", version: { version_no: "V2", total_price: 4200000, cost_total: 2730000, gross_margin: 35 } },
    { id: 6, title: "蜂巢能源模组测试线", quote_code: "QT-202601-008", status: "CONVERTED", type: "PROJECT", priority: "HIGH", customer_id: 6, customer_name: "蜂巢能源", valid_until: "2026-03-01", created_at: "2026-01-20", version: { version_no: "V1", total_price: 2200000, cost_total: 1430000, gross_margin: 35 } },
  ];

  // 模拟统计数据
  const MOCK_STATS = {
    total: 256,
    draft: 40,
    inReview: 30,
    approved: 46,
    sent: 33,
    expired: 18,
    rejected: 19,
    accepted: 44,
    converted: 19,
    totalAmount: 89500000,
    avgAmount: 349609,
    avgMargin: 35,
    conversionRate: 57.6,
    thisMonth: 28,
    lastMonth: 24,
    growth: 16.7
  };

  // 获取报价列表
  const fetchQuotes = useCallback(async () => {
    try {
      setLoading(true);
      const apiParams = {
        keyword: searchTerm || undefined,
        status: filters.status !== 'all' ? filters.status : undefined,
        customer_id: filters.customer_id !== 'all' ? filters.customer_id : undefined,
      };
      const response = await quoteApi.getQuotes(apiParams);
      const quotesData = response.data?.items || response.data?.data?.items || response.data || [];
      setQuotes(Array.isArray(quotesData) && quotesData.length > 0 ? quotesData : MOCK_QUOTES);
    } catch (error) {
      handleApiError(error, '获取报价列表');
      // API失败时使用模拟数据
      setQuotes(MOCK_QUOTES);
    } finally {
      setLoading(false);
    }
  }, [filters, searchTerm]);

  // 获取统计数据
  const fetchStats = useCallback(async () => {
    try {
      const response = await quoteApi.getStats({ timeRange });
      const statsData = response.data?.data || response.data || {};
      // 如果返回数据有效则使用，否则使用模拟数据
      if (statsData.total > 0) {
        setStats(statsData);
      } else {
        setStats(MOCK_STATS);
      }
    } catch (error) {
      handleApiError(error, '获取统计数据');
      // API失败时使用模拟数据
      setStats(MOCK_STATS);
    }
  }, [timeRange]);

  // 获取商机列表
  const fetchOpportunities = useCallback(async () => {
    try {
      const response = await opportunityApi.getOpportunities();
      setOpportunities(response.data?.items || response.data || []);
    } catch (error) {
      handleApiError(error, '获取商机列表');
      setOpportunities([]);
    }
  }, []);

  // 获取客户列表
  const fetchCustomers = useCallback(async () => {
    try {
      const response = await customerApi.getCustomers();
      setCustomers(response.data?.items || response.data || []);
    } catch (error) {
      handleApiError(error, '获取客户列表');
      setCustomers([]);
    }
  }, []);

  // 处理刷新
  const handleRefresh = useCallback(() => {
    fetchQuotes();
    fetchStats();
  }, [fetchQuotes, fetchStats]);

  // 处理查看报价详情
  const handleQuoteView = useCallback((quote) => {
    setSelectedQuote(quote);
    setShowDetailDialog(true);
  }, []);

  // 处理编辑报价
  const handleQuoteEdit = useCallback((quote) => {
    if (quote?.id) {
      navigate(`/sales/quotes/${quote.id}/edit`);
      return;
    }

    // 兜底：没有可用ID时保留旧行为
    setSelectedQuote(quote);
    setShowEditDialog(true);
  }, [navigate]);

  // 处理复制报价
  const handleQuoteCopy = useCallback((quote) => {
    // 复制报价逻辑
    console.log('Copying quote:', quote.id);
    // 可以创建新的报价并填充相同内容
  }, []);

  // 处理发送报价
  const handleQuoteSend = useCallback((quote) => {
    // 发送报价逻辑
    console.log('Sending quote:', quote.id);
  }, []);

  // 处理审批报价
  const handleQuoteApprove = useCallback((quote) => {
    // 审批报价逻辑
    console.log('Approving quote:', quote.id);
  }, []);

  // 处理拒绝报价
  const handleQuoteReject = useCallback((quote) => {
    // 拒绝报价逻辑
    console.log('Rejecting quote:', quote.id);
  }, []);

  // 处理创建报价
  const handleQuoteCreate = useCallback(() => {
    navigate("/sales/quotes/create");
  }, [navigate]);

  const loadCostInsights = useCallback(async () => {
    const now = new Date();
    let startDate;
    if (costTimeRange === "quarter") {
      startDate = new Date(
        now.getFullYear(),
        Math.floor(now.getMonth() / 3) * 3,
        1,
      );
    } else if (costTimeRange === "year") {
      startDate = new Date(now.getFullYear(), 0, 1);
    } else {
      startDate = new Date(now.getFullYear(), now.getMonth(), 1);
    }
    const endDate = now.toISOString().split("T")[0];
    const startDateStr = startDate.toISOString().split("T")[0];

    try {
      setCostLoading(true);
      const response = await purchaseApi.orders.list({
        page: 1,
        page_size: 500,
        start_date: startDateStr,
        end_date: endDate,
      });
      const orders = response.data?.items || response.data?.items || response.data || [];

      let totalCost = 0;
      const categories = new Map();
      const suppliers = new Map();
      const monthlyTrend = new Map();

      (orders || []).forEach((order) => {
        const amount = parseFloat(order.total_amount || 0);
        totalCost += amount;
        const supplier =
          order.supplier_name || order.supplier?.name || "未知供应商";
        suppliers.set(supplier, (suppliers.get(supplier) || 0) + amount);

        const dateValue = order.order_date || order.created_at;
        if (dateValue) {
          const date = new Date(dateValue);
          const monthKey = `${date.getFullYear()}-${String(
            date.getMonth() + 1,
          ).padStart(2, "0")}`;
          const entry = monthlyTrend.get(monthKey) || { amount: 0, orders: 0 };
          entry.amount += amount;
          entry.orders += 1;
          monthlyTrend.set(monthKey, entry);
        }

        order.items?.forEach((item) => {
          const category = item.material_category || item.category || "其他";
          const itemAmount = parseFloat(
            item.amount || item.unit_price * item.quantity || 0,
          );
          categories.set(category, (categories.get(category) || 0) + itemAmount);
        });
      });

      const avgOrderCost = orders?.length
        ? totalCost / orders?.length
        : 0;

      const trendArray = Array.from(monthlyTrend.entries()).sort(([a], [b]) =>
        a.localeCompare(b),
      );
      let savings = 0;
      let savingsRate = 0;
      if (trendArray.length >= 2) {
        const latest = trendArray[trendArray.length - 1][1];
        const previous = trendArray[trendArray.length - 2][1];
        const latestAvg =
          latest.orders > 0 ? latest.amount / latest.orders : 0;
        const previousAvg =
          previous.orders > 0 ? previous.amount / previous.orders : 0;
        if (previousAvg > 0 && latestAvg < previousAvg) {
          savings = (previousAvg - latestAvg) * latest.orders;
          savingsRate = ((previousAvg - latestAvg) / previousAvg) * 100;
        }
      }

      const topCategories = Array.from(categories.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 4)
        .map(([name, amount]) => ({ name, amount }));

      const topSuppliers = Array.from(suppliers.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 4)
        .map(([name, amount]) => ({ name, amount }));

      const trendList = (trendArray || []).map(([month, values]) => ({
        month,
        amount: values.amount,
        orders: values.orders
      }));

      setCostInsights({
        totalCost,
        orderCount: orders?.length,
        averageOrderCost: avgOrderCost,
        costSavings: Math.max(0, savings),
        savingsRate: Math.max(0, savingsRate),
        categories: topCategories,
        suppliers: topSuppliers,
        trend: trendList
      });
    } catch (error) {
      const { useMockData } = handleApiError(error, "加载成本洞察");
      setCostInsights(useMockData ? DEFAULT_COST_INSIGHTS : EMPTY_COST_INSIGHTS);
    } finally {
      setCostLoading(false);
    }
  }, [costTimeRange]);

  useEffect(() => {
    loadCostInsights();
  }, [loadCostInsights]);

  // 处理筛选变化
  const handleFilterChange = useCallback((newFilters) => {
    setFilters(newFilters);
  }, []);

  // 处理选择变化
  const handleSelectionChange = useCallback((newSelection) => {
    setSelectedQuotes(newSelection);
  }, []);

  // 处理导出
  const handleExport = useCallback(() => {
    // 导出逻辑
    console.log('Exporting quotes:', selectedQuotes.length);
  }, [selectedQuotes]);

  // 处理导入
  const handleImport = useCallback(() => {
    // 导入逻辑
    console.log('Import dialog opened');
  }, []);

  // 初始化数据
  useEffect(() => {
    handleRefresh();
    fetchOpportunities();
    fetchCustomers();
  }, []);

  // 当筛选条件变化时重新获取数据
  useEffect(() => {
    fetchQuotes();
  }, [filters, searchTerm]);  // 移除 sortBy，因为后端API不支持此参数

  // 当时间范围变化时重新获取统计数据
  useEffect(() => {
    fetchStats();
  }, [timeRange]);

  const topSupplier = (costInsights?.suppliers || [])[0];
  const trendItems = (costInsights?.trend || []).slice(-4);
  const categories = costInsights?.categories || [];
  const suppliers = costInsights?.suppliers || [];
  const totalCostForRatio =
    costInsights?.totalCost ||
    (categories || []).reduce((sum, item) => sum + (item.amount || 0), 0);

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="space-y-6">

      {!embedded && (
        <PageHeader
          title="报价管理"
          subtitle="管理销售报价，支持多版本管理和审批流程"
          breadcrumbs={[
          { label: "销售管理", href: "/sales" },
          { label: "报价管理", href: "/quotes" }]
          }
          actions={
          <div className="flex items-center gap-3">
              <Button
              variant="outline"
              onClick={() => window.location.href = "/quote-analytics"}>

                数据分析
              </Button>
              <Button
              onClick={handleQuoteCreate}
              className="bg-blue-600 hover:bg-blue-700 text-white">

                新建报价
              </Button>
          </div>
          } />
      )}

      {/* Tab 切换：报价列表 / 毛利分析 (仅在非嵌入模式下显示) */}
      {!embedded ? (
      <Tabs defaultValue="quotes" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2 mb-6">
          <TabsTrigger value="quotes" className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            报价列表
          </TabsTrigger>
          <TabsTrigger value="margin" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            毛利分析
          </TabsTrigger>
        </TabsList>

        <TabsContent value="quotes">
      <motion.div variants={fadeIn} className="space-y-6">
        {/* 统计概览 */}
        <QuoteStatsOverview
          stats={stats}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          onRefresh={handleRefresh}
          loading={loading}
          timeRange={timeRange}
          onTimeRangeChange={setTimeRange} />


        {/* 成本洞察 */}
        <motion.div variants={fadeIn} className="grid gap-6 xl:grid-cols-3">
          <Card className="xl:col-span-2 bg-slate-900/60 border-slate-800 text-white">
            <CardHeader className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <CardTitle className="text-lg">成本报价洞察</CardTitle>
                <p className="text-sm text-slate-400 mt-1">
                  自动汇总采购成本，辅助报价策略
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant="outline" className="text-xs border-slate-700 text-slate-300">
                  {COST_RANGE_LABELS[costTimeRange]}
                </Badge>
                <Select value={costTimeRange} onValueChange={setCostTimeRange}>
                  <SelectTrigger className="w-[130px] border-slate-700">
                    <SelectValue placeholder="选择周期" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-900 border-slate-700 text-white">
                    <SelectItem value="month">本月</SelectItem>
                    <SelectItem value="quarter">本季度</SelectItem>
                    <SelectItem value="year">本年度</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              {costLoading ? (
                <div className="space-y-4 animate-pulse">
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    {[...Array(4)].map((_, idx) => (
                      <div key={idx} className="h-24 rounded-xl bg-slate-800" />
                    ))}
                  </div>
                  <div className="h-32 rounded-xl bg-slate-800" />
                </div>
              ) : (
                <>
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <CostMetricCard
                      label="采购总额"
                      value={formatCurrency(costInsights.totalCost || 0)}
                      description={`${costInsights.orderCount || 0} 笔订单`}
                      icon={DollarSign}
                    />
                    <CostMetricCard
                      label="平均单笔金额"
                      value={formatCurrency(costInsights.averageOrderCost || 0)}
                      description="实时均价"
                      icon={PieChart}
                    />
                    <CostMetricCard
                      label="成本节约"
                      value={formatCurrency(costInsights.costSavings || 0)}
                      description={`节约率 ${formatPercent(costInsights.savingsRate || 0)}`}
                      icon={TrendingDown}
                    />
                    <CostMetricCard
                      label="核心供应商"
                      value={topSupplier?.name || "暂无数据"}
                      description={
                        topSupplier ? formatCurrency(topSupplier.amount || 0) : "等待真实数据"
                      }
                      icon={TrendingUp}
                    />
                  </div>

                  <div className="mt-6">
                    <div className="flex items-center justify-between">
                      <p className="text-sm text-slate-300">采购趋势</p>
                      <span className="text-xs text-slate-500">
                        最近 {trendItems.length || 0} 期
                      </span>
                    </div>
                    {trendItems.length === 0 ? (
                      <div className="text-sm text-slate-500 mt-4">
                        暂无趋势数据
                      </div>
                    ) : (
                      <div className="mt-4 space-y-3">
                        {(trendItems || []).map((item) => (
                          <div
                            key={item.month}
                            className="flex items-center justify-between rounded-lg border border-slate-800 px-4 py-3"
                          >
                            <div>
                              <p className="text-sm font-medium text-white">
                                {item.month}
                              </p>
                              <p className="text-xs text-slate-500 mt-1">
                                {item.orders || 0} 笔订单
                              </p>
                            </div>
                            <span className="text-base font-semibold text-emerald-400">
                              {formatCurrency(item.amount || 0)}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-slate-800 text-white">
            <CardHeader>
              <CardTitle className="text-lg">成本结构与供应商</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {costLoading ? (
                <div className="space-y-4 animate-pulse">
                  {[...Array(4)].map((_, idx) => (
                    <div key={idx} className="h-14 rounded-lg bg-slate-800" />
                  ))}
                </div>
              ) : (
                <>
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-sm text-slate-300">成本构成</p>
                      <Badge variant="secondary" className="bg-blue-500/10 text-blue-300">
                        TOP 分类
                      </Badge>
                    </div>
                    {categories?.length === 0 ? (
                      <p className="text-sm text-slate-500">暂无成本分类数据</p>
                    ) : (
                      <div className="space-y-3">
                        {(categories || []).map((cat) => {
                          const percent = totalCostForRatio
                            ? Math.round((cat.amount / totalCostForRatio) * 100)
                            : 0;
                          return (
                            <div key={cat.name} className="space-y-1">
                              <div className="flex items-center justify-between text-sm">
                                <span>{cat.name}</span>
                                <span className="text-slate-300">
                                  {formatCurrency(cat.amount || 0)}
                                </span>
                              </div>
                              <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                                <div
                                  className="h-full bg-blue-500"
                                  style={{ width: `${Math.min(Math.max(percent, 3), 100)}%` }}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-sm text-slate-300">优选供应商</p>
                      <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-300">
                        TOP 供应商
                      </Badge>
                    </div>
                    {suppliers.length === 0 ? (
                      <p className="text-sm text-slate-500">暂无供应商数据</p>
                    ) : (
                      <div className="space-y-3">
                        {(suppliers || []).map((supplier, index) => (
                          <div
                            key={supplier.name}
                            className="flex items-center justify-between rounded-lg border border-slate-800 px-3 py-2"
                          >
                            <div>
                              <p className="text-sm text-white font-medium">
                                {supplier.name}
                              </p>
                              <p className="text-xs text-slate-500 mt-1">
                                采购额 {formatCurrency(supplier.amount || 0)}
                              </p>
                            </div>
                            <Badge variant="outline" className="border-slate-700 text-slate-300">
                              TOP {index + 1}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* 报价列表管理 */}
        <QuoteListManager
          quotes={quotes}
          opportunities={opportunities}
          customers={customers}
          viewMode={viewMode}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          filters={filters}
          onFilterChange={handleFilterChange}
          sortBy={sortBy}
          onSortChange={setSortBy}
          selectedQuotes={selectedQuotes}
          onSelectionChange={handleSelectionChange}
          onQuoteView={handleQuoteView}
          onQuoteEdit={handleQuoteEdit}
          onQuoteCreate={handleQuoteCreate}
          onQuoteCopy={handleQuoteCopy}
          onQuoteSend={handleQuoteSend}
          onQuoteApprove={handleQuoteApprove}
          onQuoteReject={handleQuoteReject}
          onExport={handleExport}
          onImport={handleImport}
          loading={loading} />

      </motion.div>
        </TabsContent>

        <TabsContent value="margin">
          <MarginAnalysis />
        </TabsContent>
      </Tabs>
      ) : (
        // embedded 模式：直接显示报价列表，毛利分析由父组件处理
        <motion.div variants={fadeIn} className="space-y-6">
          <QuoteStatsOverview
            stats={stats}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            onRefresh={handleRefresh}
            loading={loading}
            timeRange={timeRange}
            onTimeRangeChange={setTimeRange}
          />
          <QuoteListManager
            quotes={quotes}
            opportunities={opportunities}
            customers={customers}
            viewMode={viewMode}
            searchTerm={searchTerm}
            onSearchChange={setSearchTerm}
            filters={filters}
            onFilterChange={handleFilterChange}
            sortBy={sortBy}
            onSortChange={setSortBy}
            selectedQuotes={selectedQuotes}
            onSelectionChange={handleSelectionChange}
            onQuoteView={handleQuoteView}
            onQuoteEdit={handleQuoteEdit}
            onQuoteCreate={handleQuoteCreate}
            onQuoteCopy={handleQuoteCopy}
            onQuoteSend={handleQuoteSend}
            onQuoteApprove={handleQuoteApprove}
            onQuoteReject={handleQuoteReject}
            onExport={handleExport}
            onImport={handleImport}
            loading={loading}
          />
        </motion.div>
      )}

      {/* 报价详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 text-white max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              报价详情
              <span className="text-sm text-slate-400">#{selectedQuote?.id}</span>
            </DialogTitle>
          </DialogHeader>
          {selectedQuote &&
          <div className="space-y-6">
              {/* 基本信息 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-slate-400">标题</label>
                  <p className="text-white font-medium">{selectedQuote.title}</p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">状态</label>
                  <div className="mt-1">
                    <span className="px-2 py-1 bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded text-sm">
                      {selectedQuote.status}
                    </span>
                  </div>
                </div>
                <div>
                  <label className="text-sm text-slate-400">类型</label>
                  <p className="text-white">{selectedQuote.type}</p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">优先级</label>
                  <p className="text-white">{selectedQuote.priority}</p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">客户</label>
                  <p className="text-white">{selectedQuote.customer_name}</p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">有效期至</label>
                  <p className="text-white">
                    {selectedQuote.valid_until ? new Date(selectedQuote.valid_until).toLocaleDateString() : '未设置'}
                  </p>
                </div>
              </div>

              {/* 版本信息 */}
              {selectedQuote.version &&
            <div>
                  <label className="text-sm text-slate-400 block mb-2">版本信息</label>
                  <div className="bg-slate-800/60 rounded-lg p-4 space-y-2">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-slate-500">版本号:</span>
                        <span className="text-white ml-2">{selectedQuote.version.version_no}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">总金额:</span>
                        <span className="text-emerald-400 ml-2">
                          ¥{selectedQuote.version.total_price?.toLocaleString()}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500">成本:</span>
                        <span className="text-red-400 ml-2">
                          ¥{selectedQuote.version.cost_total?.toLocaleString()}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500">毛利率:</span>
                        <span className="text-blue-400 ml-2">
                          {selectedQuote.version.gross_margin}%
                        </span>
                      </div>
                    </div>
                  </div>
            </div>
            }

              {/* 操作按钮 */}
              <div className="flex justify-end gap-3 pt-4 border-t border-slate-700">
                <Button
                variant="outline"
                onClick={() => setShowDetailDialog(false)}>

                  关闭
                </Button>
                <Button
                onClick={() => {
                  handleQuoteEdit(selectedQuote);
                  setShowDetailDialog(false);
                }}>

                  编辑
                </Button>
                <Button
                onClick={() => {
                  handleQuoteSend(selectedQuote);
                  setShowDetailDialog(false);
                }}>

                  发送
                </Button>
              </div>
          </div>
          }
        </DialogContent>
      </Dialog>

      {/* 创建报价对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl bg-slate-900 border-slate-700 text-white">
          <DialogHeader>
            <DialogTitle>新建报价</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-slate-400">为保证字段完整性，请在独立页面创建报价。</p>
            <div className="flex justify-end gap-3 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowCreateDialog(false)}>

                取消
              </Button>
              <Button
                onClick={() => {
                  setShowCreateDialog(false);
                  navigate("/sales/quotes/create");
                }}>
                去创建页
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 编辑报价对话框 */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-2xl bg-slate-900 border-slate-700 text-white">
          <DialogHeader>
            <DialogTitle>编辑报价</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-slate-400">编辑请跳转到报价编辑页，避免字段丢失。</p>
            <div className="flex justify-end gap-3 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowEditDialog(false)}>

                取消
              </Button>
              <Button
                onClick={() => {
                  setShowEditDialog(false);
                  if (selectedQuote?.id) {
                    navigate(`/sales/quotes/${selectedQuote.id}/edit`);
                  }
                }}>
                去编辑页
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </motion.div>);

}

function CostMetricCard({ label, value, description, icon: Icon }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 space-y-2">
      <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-400">
        {Icon && <Icon className="h-4 w-4 text-slate-300" />}
        {label}
      </div>
      <div className="text-2xl font-semibold text-white">{value}</div>
      {description && <p className="text-xs text-slate-500">{description}</p>}
    </div>
  );
}
