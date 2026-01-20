/**
 * Procurement Manager Dashboard - Main dashboard for procurement department manager
 * Features: Team management, Supplier management, Purchase approval, Cost analysis, Performance monitoring
 */

import { useState, useMemo, useEffect, useCallback } from "react";
import {
  ShoppingCart,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  ApiIntegrationError 
} from "../components/ui";
import { purchaseApi, supplierApi } from "../services/api";
import {
  StatsCards,
  PerformanceMetrics,
  OverviewTab,
  ApprovalsTab,
  SuppliersTab,
  TeamTab,
  CostAnalysisTab,
  AlertsTab,
} from "../components/procurement-manager-dashboard";

export default function ProcurementManagerDashboard() {
  const [selectedTab, setSelectedTab] = useState("overview");
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [_loading, setLoading] = useState(true);
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
        page_size: 100
      }),
      purchaseApi.orders.list({
        status: "CONFIRMED",
        page: 1,
        page_size: 100
      }),
      purchaseApi.orders.list({ page: 1, page_size: 100 })]
      );

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
        is_active: true
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
        0
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
        parseFloat(order.total_amount || 0) > 100000 ?
        "high" :
        parseFloat(order.total_amount || 0) > 50000 ?
        "medium" :
        "low",
        daysPending: order.created_at ?
        Math.floor(
          (new Date() - new Date(order.created_at)) / (1000 * 60 * 60 * 24)
        ) :
        0
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
        activeTeamMembers: 0
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
  }, [pendingApprovals, searchQuery, filterStatus]);

  // Show error state
  if (error && !stats) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="采购经理仪表板"
          description="团队管理、供应商管理、采购审批、成本分析、绩效监控" />

        <ApiIntegrationError
          error={error}
          apiEndpoint="/api/v1/purchase/orders"
          onRetry={loadStatistics} />

      </div>);

  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <PageHeader
        title="采购管理"
        subtitle="采购部经理工作台"
        icon={ShoppingCart} />


      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Statistics Cards */}
        <StatsCards stats={stats} />

        {/* Additional Stats Row */}
        <PerformanceMetrics stats={stats} />

        {/* Main Content Tabs */}
        <Tabs
          value={selectedTab}
          onValueChange={setSelectedTab}
          className="space-y-6">

          <TabsList className="bg-surface-50 border-white/10">
            <TabsTrigger value="overview">采购概览</TabsTrigger>
            <TabsTrigger value="approvals">订单审批</TabsTrigger>
            <TabsTrigger value="suppliers">供应商管理</TabsTrigger>
            <TabsTrigger value="team">团队管理</TabsTrigger>
            <TabsTrigger value="cost">成本分析</TabsTrigger>
            <TabsTrigger value="alerts">预警监控</TabsTrigger>
          </TabsList>

          <OverviewTab stats={stats} recentApprovals={filteredApprovals.slice(0, 4)} />

          <TabsContent value="approvals">
            <ApprovalsTab
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              filterStatus={filterStatus}
              setFilterStatus={setFilterStatus}
              approvals={filteredApprovals}
            />
          </TabsContent>

          <TabsContent value="suppliers">
            <SuppliersTab suppliers={suppliers} />
          </TabsContent>

          <TabsContent value="team">
            <TeamTab />
          </TabsContent>

          <TabsContent value="cost">
            <CostAnalysisTab />
          </TabsContent>

          <TabsContent value="alerts">
            <AlertsTab />
          </TabsContent>
        </Tabs>
      </div>
    </div>);

}
