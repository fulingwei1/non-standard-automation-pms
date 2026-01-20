/**
 * Sales Director Workstation - Refactored
 * 销售总监工作站 - 重构版本
 * Features: Strategic overview, Team performance, Sales analytics, Revenue monitoring
 * Core Functions: Sales strategy, Team management, Performance monitoring, Contract approval
 */

import { useState, useEffect, useCallback, useMemo as _useMemo } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  TrendingUp,
  Users,
  Target,
  BarChart3,
  PieChart,
  FileText,
  Settings,
  AlertTriangle,
  Activity } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Button,
  Badge } from
"../components/ui";
import {
  salesStatisticsApi,
  salesTeamApi,
  salesTargetApi,
  salesReportApi,
  opportunityApi,
  contractApi,
  invoiceApi,
  paymentApi } from
"../services/api";
import { ApiIntegrationError } from "../components/ui";
import {
  SalesDirectorStatsOverview,
  SalesTeamPerformance,
  REPORT_TYPES,
  ALERT_TYPES,
  getPeriodRange,
  toISODate,
  calculateTrend as _calculateTrend,
  formatCurrency } from
"../components/sales-director";

export default function SalesDirectorWorkstation() {
  const navigate = useNavigate();
  const [selectedTab, setSelectedTab] = useState("overview");
  const [selectedPeriod, setSelectedPeriod] = useState("month");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // API数据状态
  const [overallStats, setOverallStats] = useState(null);
  const [teamPerformance, setTeamPerformance] = useState([]);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [topCustomers, setTopCustomers] = useState([]);
  const [_funnelData, setFunnelData] = useState(null);
  const [recentActivities, setRecentActivities] = useState([]);
  const [_teamInsights, setTeamInsights] = useState(null);
  const [rankingConfig, setRankingConfig] = useState(null);

  // 数据加载函数
  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const range = getPeriodRange(selectedPeriod);
      const rangeParams = {
        start_date: toISODate(range.start),
        end_date: toISODate(range.end)
      };
      const yearStart = new Date(range.start.getFullYear(), 0, 1);
      const yearParams = {
        start_date: toISODate(yearStart),
        end_date: toISODate(range.end)
      };
      const monthLabel = `${range.start.getFullYear()}-${String(range.start.getMonth() + 1).padStart(2, "0")}`;

      // 并行加载所有数据
      const results = await Promise.allSettled([
      salesStatisticsApi.summary(rangeParams),
      salesStatisticsApi.summary(yearParams),
      salesStatisticsApi.funnel(rangeParams),
      salesTeamApi.getTeam({ page_size: 50, ...rangeParams }),
      contractApi.list({ status: "IN_REVIEW", page_size: 5 }),
      salesReportApi.customerContribution({ top_n: 4, ...yearParams }),
      paymentApi.getStatistics(yearParams),
      opportunityApi.list({ page: 1, page_size: 5 }),
      invoiceApi.list({ page: 1, page_size: 5 }),
      salesTargetApi.list({
        target_scope: "DEPARTMENT",
        target_period: "MONTHLY",
        period_value: monthLabel,
        page_size: 1
      }),
      salesTargetApi.list({
        target_scope: "DEPARTMENT",
        target_period: "YEARLY",
        period_value: String(range.start.getFullYear()),
        page_size: 1
      })]
      );

      // 处理成功的API调用
      const [
      monthlyStats,
      yearlyStats,
      funnel,
      team,
      contracts,
      customers,
      _payments,
      opportunities,
      invoices,
      _monthlyTarget,
      _yearlyTarget] =
      results.map((result) => result.status === 'fulfilled' ? result.value : null);

      // 构建综合统计数据
      const monthlyData = monthlyStats?.data;
      const yearlyData = yearlyStats?.data;
      const teamData = team?.data?.results || [];

      setOverallStats({
        monthlyRevenue: monthlyData?.revenue || 0,
        lastMonthRevenue: monthlyData?.lastMonthRevenue || 0,
        yearlyRevenue: yearlyData?.revenue || 0,
        lastYearRevenue: yearlyData?.lastYearRevenue || 0,
        teamSize: teamData.length,
        teamGrowth: yearlyData?.teamGrowth || 0,
        activeDeals: monthlyData?.activeDeals || 0,
        lastPeriodDeals: monthlyData?.lastPeriodDeals || 0,
        conversionRate: monthlyData?.conversionRate || 0,
        lastConversionRate: monthlyData?.lastConversionRate || 0,
        avgDealSize: monthlyData?.avgDealSize || 0,
        lastAvgDealSize: monthlyData?.lastAvgDealSize || 0
      });

      setTeamPerformance(teamData.map((member) => ({
        ...member,
        performanceScore: calculatePerformanceScore(member, monthlyData?.metrics || {}),
        totalRevenue: member.totalRevenue || 0,
        dealCount: member.dealCount || 0,
        conversionRate: member.conversionRate || 0,
        avgDealSize: member.avgDealSize || 0
      })));

      setPendingApprovals(contracts?.data?.results || []);
      setTopCustomers(customers?.data?.results || []);
      setFunnelData(funnel?.data);
      setRecentActivities([
      ...(opportunities?.data?.results || []).map((o) => ({ type: 'opportunity', ...o })),
      ...(invoices?.data?.results || []).map((i) => ({ type: 'invoice', ...i }))]
      );

      setTeamInsights(yearlyData?.insights);

    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [selectedPeriod]);

  // 计算绩效得分
  const calculatePerformanceScore = (member, _metrics) => {
    const weights = {
      revenue: 0.4,
      deals: 0.2,
      conversion: 0.2,
      efficiency: 0.2
    };

    const revenueScore = Math.min((member.totalRevenue || 0) / 1000000 * 100, 100);
    const dealsScore = Math.min((member.dealCount || 0) * 10, 100);
    const conversionScore = (member.conversionRate || 0) * 5;
    const efficiencyScore = member.efficiency || 80;

    return Math.round(
      revenueScore * weights.revenue +
      dealsScore * weights.deals +
      conversionScore * weights.conversion +
      efficiencyScore * weights.efficiency
    );
  };

  // 初始数据加载
  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  // 定时刷新数据
  useEffect(() => {
    const interval = setInterval(() => {
      loadDashboard();
    }, 300000); // 5分钟刷新一次

    return () => clearInterval(interval);
  }, [loadDashboard]);

  // 处理配置更新
  const handleConfigUpdate = useCallback(async (newConfig) => {
    try {
      await salesTeamApi.updateRankingConfig(newConfig);
      setRankingConfig({ metrics: newConfig });
    } catch (err) {
      throw new Error('配置保存失败: ' + err.message);
    }
  }, []);

  // 处理成员详情查看
  const handleViewMemberDetail = useCallback((member) => {
    if (!member) {return;}
    navigate("/sales/team", { state: { openMember: member } });
  }, [navigate]);

  // Tab配置
  const tabs = [
  { value: "overview", label: "总览", icon: LayoutDashboard },
  { value: "performance", label: "团队绩效", icon: Users },
  { value: "analytics", label: "分析报表", icon: BarChart3 },
  { value: "forecast", label: "销售预测", icon: TrendingUp },
  { value: "customers", label: "客户分析", icon: Target }];


  // 渲染错误状态
  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <ApiIntegrationError
          title="销售总监工作站加载失败"
          description="无法连接到销售管理系统，请检查网络连接或联系管理员。"
          onRetry={loadDashboard} />

      </div>);

  }

  return (
    <div className="container mx-auto px-4 py-6 space-y-6">
      {/* 页面头部 */}
      <PageHeader
        title="销售总监工作站"
        subtitle="战略销售管理和团队绩效监控平台"
        icon={TrendingUp}
        actions={[
        {
          label: "刷新数据",
          icon: Activity,
          onClick: loadDashboard,
          loading: loading
        },
        {
          label: "系统设置",
          icon: Settings,
          onClick: () => console.log('Open settings')
        }]
        } />


      {/* 主要内容区域 */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <TabsTrigger key={tab.value} value={tab.value} className="flex items-center gap-2">
                <Icon className="w-4 h-4" />
                <span className="hidden sm:inline">{tab.label}</span>
              </TabsTrigger>);

          })}
        </TabsList>

        {/* 总览 */}
        <TabsContent value="overview" className="space-y-6">
          <SalesDirectorStatsOverview
            overallStats={overallStats}
            selectedPeriod={selectedPeriod}
            onPeriodChange={setSelectedPeriod}
            loading={loading}
            onRefresh={loadDashboard} />


          {/* 快速信息面板 */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 待审批合同 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-orange-600" />
                  待审批合同
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {pendingApprovals.slice(0, 3).map((contract) =>
                  <div key={contract.id} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700">
                      <div className="flex-1">
                        <div className="font-medium text-slate-100">{contract.contractName}</div>
                        <div className="text-sm text-slate-400">
                          {formatCurrency(contract.amount)} · {contract.customerName}
                        </div>
                      </div>
                      <Badge variant="outline" className="text-orange-400 border-orange-500/50">
                        待审批
                      </Badge>
                  </div>
                  )}
                  {pendingApprovals.length === 0 &&
                  <div className="text-center text-slate-500 py-4">
                      暂无待审批合同
                  </div>
                  }
                </div>
              </CardContent>
            </Card>

            {/* 重要客户 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-blue-600" />
                  重要客户
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {topCustomers.slice(0, 3).map((customer, index) =>
                  <div key={customer.id} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-sm font-medium text-blue-400">
                          {index + 1}
                        </div>
                        <div>
                          <div className="font-medium text-slate-100">{customer.customerName}</div>
                          <div className="text-sm text-slate-400">
                            {formatCurrency(customer.revenue)}
                          </div>
                        </div>
                      </div>
                  </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* 最近活动 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-5 h-5 text-green-600" />
                  最近活动
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {recentActivities.slice(0, 3).map((activity, _index) =>
                  <div key={`${activity.type}-${activity.id}`} className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg border border-slate-700">
                      <div className="w-2 h-2 rounded-full bg-green-500" />
                      <div className="flex-1">
                        <div className="text-sm text-slate-200">
                          {activity.type === 'opportunity' ? '新商机' : '新发票'}: {activity.name || activity.title}
                        </div>
                        <div className="text-xs text-slate-500">
                          {new Date(activity.createdAt || activity.createTime).toLocaleDateString()}
                        </div>
                      </div>
                  </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 团队绩效 */}
        <TabsContent value="performance" className="space-y-6">
          <SalesTeamPerformance
            teamPerformance={teamPerformance}
            rankingConfig={rankingConfig}
            configLoading={loading}
            configSaving={loading}
            onConfigUpdate={handleConfigUpdate}
            onViewMemberDetail={handleViewMemberDetail} />

        </TabsContent>

        {/* 分析报表 */}
        <TabsContent value="analytics" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-purple-600" />
                销售分析报表
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <BarChart3 className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-100 mb-2">分析报表组件</h3>
                <p className="text-slate-400">销售分析报表功能正在开发中...</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 销售预测 */}
        <TabsContent value="forecast" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-indigo-600" />
                销售预测
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <TrendingUp className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-100 mb-2">销售预测组件</h3>
                <p className="text-slate-400">销售预测功能正在开发中...</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 客户分析 */}
        <TabsContent value="customers" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5 text-cyan-600" />
                客户分析
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <Target className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-100 mb-2">客户分析组件</h3>
                <p className="text-slate-400">客户分析功能正在开发中...</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>);

}
