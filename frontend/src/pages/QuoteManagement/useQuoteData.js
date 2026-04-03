/**
 * useQuoteData - Custom hook for quote management data fetching and state
 * 报价管理数据获取和状态管理 Hook
 */

import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { DEFAULT_QUOTE_STATS } from "../../components/quote";
import { quoteApi, opportunityApi, customerApi, purchaseApi } from "../../services/api";
import { handleApiError } from "../../utils/apiErrorHandler";
import { EMPTY_COST_INSIGHTS } from "./constants";

export default function useQuoteData() {
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
  const [costInsights, setCostInsights] = useState(EMPTY_COST_INSIGHTS);
  const [costLoading, setCostLoading] = useState(false);

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
      setQuotes(Array.isArray(quotesData) ? quotesData : []);
    } catch (error) {
      handleApiError(error, '获取报价列表');
      setQuotes([]);
    } finally {
      setLoading(false);
    }
  }, [filters, searchTerm]);

  // 获取统计数据
  const fetchStats = useCallback(async () => {
    try {
      const response = await quoteApi.getStats({ timeRange });
      const statsData = response.data?.data || response.data || {};
      setStats(statsData.total > 0 ? statsData : DEFAULT_QUOTE_STATS);
    } catch (error) {
      handleApiError(error, '获取统计数据');
      setStats(DEFAULT_QUOTE_STATS);
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
    console.log('Copying quote:', quote.id);
  }, []);

  // 处理发送报价
  const handleQuoteSend = useCallback((quote) => {
    console.log('Sending quote:', quote.id);
  }, []);

  // 处理审批报价
  const handleQuoteApprove = useCallback((quote) => {
    console.log('Approving quote:', quote.id);
  }, []);

  // 处理拒绝报价
  const handleQuoteReject = useCallback((quote) => {
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
      handleApiError(error, "加载成本洞察");
      setCostInsights(EMPTY_COST_INSIGHTS);
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
    console.log('Exporting quotes:', selectedQuotes.length);
  }, [selectedQuotes]);

  // 处理导入
  const handleImport = useCallback(() => {
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

  // Derived data
  const topSupplier = (costInsights?.suppliers || [])[0];
  const trendItems = (costInsights?.trend || []).slice(-4);
  const categoriesList = costInsights?.categories || [];
  const suppliersList = costInsights?.suppliers || [];
  const totalCostForRatio =
    costInsights?.totalCost ||
    (categoriesList || []).reduce((sum, item) => sum + (item.amount || 0), 0);

  return {
    // State
    quotes,
    opportunities,
    customers,
    selectedQuotes,
    loading,
    showCreateDialog,
    setShowCreateDialog,
    showEditDialog,
    setShowEditDialog,
    showDetailDialog,
    setShowDetailDialog,
    selectedQuote,
    stats,
    viewMode,
    setViewMode,
    searchTerm,
    setSearchTerm,
    filters,
    sortBy,
    setSortBy,
    timeRange,
    setTimeRange,
    costTimeRange,
    setCostTimeRange,
    costInsights,
    costLoading,

    // Handlers
    handleRefresh,
    handleQuoteView,
    handleQuoteEdit,
    handleQuoteCopy,
    handleQuoteSend,
    handleQuoteApprove,
    handleQuoteReject,
    handleQuoteCreate,
    handleFilterChange,
    handleSelectionChange,
    handleExport,
    handleImport,

    // Derived
    topSupplier,
    trendItems,
    categories: categoriesList,
    suppliers: suppliersList,
    totalCostForRatio,
  };
}
