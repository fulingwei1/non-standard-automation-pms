/**
 * Sales Director Workstation - Executive dashboard for sales directors
 * Features: Strategic overview, Team performance, Sales analytics, Revenue monitoring
 * Core Functions: Sales strategy, Team management, Performance monitoring, Contract approval
 */

import { useState, useEffect, useCallback } from "react";
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
  Loader2,
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
} from "../components/ui";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import {
  salesStatisticsApi,
  salesTeamApi,
  salesTargetApi,
  salesReportApi,
  opportunityApi,
  contractApi,
  invoiceApi,
  paymentApi,
} from "../services/api";
import { ApiIntegrationError } from "../components/ui";

const DEFAULT_STATS = {
  monthlyTarget: 5000000,
  yearTarget: 60000000,
};

const formatCurrency = (value) => {
  if (value >= 10000) {
    return `¥${(value / 10000).toFixed(1)}万`;
  }
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
    minimumFractionDigits: 0,
  }).format(value);
};

const toISODate = (value) => value.toISOString().split("T")[0];

const getPeriodRange = (period) => {
  const now = new Date();
  if (period === "quarter") {
    const start = new Date(now.getFullYear(), now.getMonth() - 2, 1);
    return { start, end: now };
  }
  if (period === "year") {
    const start = new Date(now.getFullYear(), 0, 1);
    return { start, end: now };
  }
  const start = new Date(now.getFullYear(), now.getMonth(), 1);
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  return { start, end };
};

const transformTeamMember = (member) => ({
  id: member.user_id,
  name: member.user_name,
  role: member.role,
  monthlyAchieved: member.monthly_actual || member.contract_amount || 0,
  monthlyTarget: member.monthly_target || 0,
  achievementRate: Math.round(member.monthly_completion_rate || 0),
  activeProjects: member.contract_count || 0,
  newCustomers: member.new_customers || 0,
});

const transformApprovalItem = (contract) => ({
  id: contract.id,
  type: "contract",
  title: contract.contract_code || contract.contract_name || "合同审批",
  customer: contract.customer_name || "未命名客户",
  amount: Number(contract.contract_amount || 0),
  submitter: contract.owner_name || "系统",
  submitTime: contract.created_at || "",
  priority: Number(contract.contract_amount || 0) > 500000 ? "high" : "medium",
});

const transformContributionCustomer = (item) => ({
  id: item.customer_id || item.customer_name,
  name: item.customer_name || "未命名客户",
  totalAmount: item.total_amount || 0,
  thisYear: item.total_amount || 0,
  projectCount: item.contract_count || 0,
});

const buildRecentActivities = (opps, invoices, approvals) => {
  const activities = [];
  opps.forEach((opp) => {
    activities.push({
      id: `opp-${opp.id}`,
      type: "opportunity_created",
      action: "新增商机",
      target: opp.opportunity_name || opp.name || opp.opportunity_code,
      operator: opp.owner?.real_name || opp.owner_name || "销售团队",
      timestamp: opp.created_at || opp.updated_at || new Date().toISOString(),
      status: "success",
    });
  });
  invoices.forEach((invoice) => {
    activities.push({
      id: `invoice-${invoice.id}`,
      type:
        invoice.payment_status === "PAID"
          ? "payment_received"
          : "invoice_issued",
      action: invoice.payment_status === "PAID" ? "收到回款" : "发票开具",
      target: invoice.invoice_code || `合同 ${invoice.contract_code || ""}`,
      operator: invoice.approver_name || "财务部",
      timestamp:
        invoice.paid_date ||
        invoice.issue_date ||
        invoice.created_at ||
        new Date().toISOString(),
      status: invoice.payment_status === "PAID" ? "success" : "pending",
    });
  });
  approvals.forEach((approval) => {
    activities.push({
      id: `approval-${approval.id}`,
      type: "contract_review",
      action: "合同审批",
      target: approval.title,
      operator: approval.submitter,
      timestamp: approval.submitTime || new Date().toISOString(),
      status: "pending",
    });
  });

  return activities
    .filter((item) => item.timestamp)
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    .slice(0, 6);
};

const formatTimelineLabel = (value) => {
  if (!value) return "刚刚";
  try {
    return new Date(value).toLocaleString("zh-CN", { hour12: false });
  } catch (err) {
    return value;
  }
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
          {trend && (
            <div className="flex items-center gap-1 mt-2">
              {trend > 0 ? (
                <>
                  <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">+{trend}%</span>
                </>
              ) : (
                <>
                  <ArrowDownRight className="w-3 h-3 text-red-400" />
                  <span className="text-xs text-red-400">{trend}%</span>
                </>
              )}
              <span className="text-xs text-slate-500 ml-1">vs 上月</span>
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

export default function SalesDirectorWorkstation() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [overallStats, setOverallStats] = useState(null);
  const [teamPerformance, setTeamPerformance] = useState([]);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [topCustomers, setTopCustomers] = useState([]);
  const [funnelData, setFunnelData] = useState(null);
  const [recentActivities, setRecentActivities] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState("month");

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const range = getPeriodRange(selectedPeriod);
      const rangeParams = {
        start_date: toISODate(range.start),
        end_date: toISODate(range.end),
      };
      const yearStart = new Date(range.start.getFullYear(), 0, 1);
      const yearParams = {
        start_date: toISODate(yearStart),
        end_date: toISODate(range.end),
      };
      const monthLabel = `${range.start.getFullYear()}-${String(range.start.getMonth() + 1).padStart(2, "0")}`;

      // 使用 Promise.allSettled 来捕获所有API调用的结果，包括失败的
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
          page_size: 1,
        }),
        salesTargetApi.list({
          target_scope: "DEPARTMENT",
          target_period: "YEARLY",
          period_value: String(range.start.getFullYear()),
          page_size: 1,
        }),
      ]);

      // 检查是否有失败的请求
      const failedRequests = results
        .map((result, index) => ({ result, index }))
        .filter(({ result }) => result.status === "rejected");

      if (failedRequests.length > 0) {
        // 记录所有失败的请求
        console.error(
          "Failed API requests:",
          failedRequests.map((f) => ({
            index: f.index,
            error:
              f.result.reason?.response?.data ||
              f.result.reason?.message ||
              f.result.reason,
          })),
        );

        // 找到第一个失败的请求并抛出错误
        const firstFailed = failedRequests[0];
        const apiNames = [
          "salesStatisticsApi.summary (monthly)",
          "salesStatisticsApi.summary (yearly)",
          "salesStatisticsApi.funnel",
          "salesTeamApi.getTeam",
          "contractApi.list",
          "salesReportApi.customerContribution",
          "paymentApi.getStatistics",
          "opportunityApi.list",
          "invoiceApi.list",
          "salesTargetApi.list (monthly)",
          "salesTargetApi.list (yearly)",
        ];
        const error = firstFailed.result.reason;
        error.apiName = apiNames[firstFailed.index];
        error.apiIndex = firstFailed.index;
        console.error(
          `First failed API: ${error.apiName} (index: ${firstFailed.index})`,
          error,
        );
        throw error;
      }

      // 提取成功的结果
      const [
        monthlySummaryRes,
        yearlySummaryRes,
        funnelRes,
        teamRes,
        approvalsRes,
        customersRes,
        paymentStatsRes,
        opportunitiesRes,
        invoicesRes,
        monthTargetsRes,
        yearTargetsRes,
      ] = results.map((r) => r.value);

      const extractData = (res) => res?.data?.data || res?.data || res || {};
      const summaryMonth = extractData(monthlySummaryRes);
      const summaryYear = extractData(yearlySummaryRes);
      const funnelPayload = extractData(funnelRes) || {};
      const teamMembers =
        teamRes?.data?.team_members ||
        teamRes?.data?.data?.team_members ||
        teamRes?.team_members ||
        [];
      const approvals = approvalsRes?.data?.items || approvalsRes?.data || [];
      const customerContribution = extractData(customersRes)?.customers || [];
      const paymentSummary = extractData(paymentStatsRes)?.summary || {};
      const opportunities =
        opportunitiesRes?.data?.items || opportunitiesRes?.data || [];
      const invoices = invoicesRes?.data?.items || invoicesRes?.data || [];
      const monthTarget = monthTargetsRes?.data?.items?.[0];
      const yearTarget = yearTargetsRes?.data?.items?.[0];

      const normalizedTeam = teamMembers
        .map(transformTeamMember)
        .sort((a, b) => (b.monthlyAchieved || 0) - (a.monthlyAchieved || 0))
        .slice(0, 4);
      setTeamPerformance(normalizedTeam);

      const approvalsTransformed = approvals.map(transformApprovalItem);
      setPendingApprovals(approvalsTransformed);

      const customersTransformed = customerContribution.map(
        transformContributionCustomer,
      );
      setTopCustomers(customersTransformed);

      const activities = buildRecentActivities(
        opportunities,
        invoices,
        approvalsTransformed,
      );
      setRecentActivities(activities);

      const monthlyAchieved = summaryMonth?.total_contract_amount || 0;
      const monthlyTargetValue =
        monthTarget?.target_value ||
        summaryMonth?.monthly_target ||
        DEFAULT_STATS.monthlyTarget;
      const achievementRate =
        monthlyTargetValue > 0
          ? (monthlyAchieved / monthlyTargetValue) * 100
          : 0;
      const yearAchieved = summaryYear?.total_contract_amount || 0;
      const yearTargetValue =
        yearTarget?.target_value ||
        summaryYear?.year_target ||
        monthlyTargetValue * 12;
      const yearProgress =
        yearTargetValue > 0 ? (yearAchieved / yearTargetValue) * 100 : 0;

      const customerTotal = teamMembers.reduce(
        (sum, member) => sum + (member.customer_total || 0),
        0,
      );
      const newCustomers = teamMembers.reduce(
        (sum, member) => sum + (member.new_customers || 0),
        0,
      );

      setOverallStats({
        monthlyTarget: monthlyTargetValue,
        monthlyAchieved,
        achievementRate,
        customerCount: customerTotal,
        newCustomers,
        activeContracts: summaryMonth?.signed_contracts || 0,
        pendingContracts: approvalsTransformed.length,
        pendingPayment: paymentSummary.total_unpaid || 0,
        overduePayment: paymentSummary.total_overdue || 0,
        collectionRate: paymentSummary.collection_rate || 0,
        yearTarget: yearTargetValue,
        yearAchieved,
        yearProgress,
        activeOpportunities: summaryMonth?.total_opportunities || 0,
        hotOpportunities: summaryMonth?.won_opportunities || 0,
      });

      setFunnelData({
        inquiry: {
          count: funnelPayload.leads || 0,
          amount: funnelPayload.total_opportunity_amount || 0,
          conversion: 100,
        },
        qualification: {
          count: funnelPayload.opportunities || 0,
          amount: funnelPayload.total_opportunity_amount || 0,
          conversion: funnelPayload.conversion_rates?.lead_to_opp || 0,
        },
        proposal: {
          count: funnelPayload.quotes || 0,
          amount: funnelPayload.total_opportunity_amount || 0,
          conversion: funnelPayload.conversion_rates?.opp_to_quote || 0,
        },
        negotiation: {
          count: Math.max(
            (funnelPayload.opportunities || 0) - (funnelPayload.contracts || 0),
            0,
          ),
          amount: funnelPayload.total_opportunity_amount || 0,
          conversion: funnelPayload.conversion_rates?.quote_to_contract || 0,
        },
        closed: {
          count: funnelPayload.contracts || 0,
          amount: funnelPayload.total_contract_amount || 0,
          conversion: funnelPayload.conversion_rates?.quote_to_contract || 0,
        },
      });
    } catch (err) {
      console.error("Failed to load sales director data:", err);
      console.error("Error details:", {
        message: err?.message,
        response: err?.response?.data,
        status: err?.response?.status,
        apiName: err?.apiName,
        apiIndex: err?.apiIndex,
        url: err?.config?.url,
      });

      // 提取错误信息字符串，避免直接传递对象给 React 渲染
      const errorMsg = err?.response?.data?.detail;
      let errorStr = "加载数据失败";
      if (typeof errorMsg === "string") {
        errorStr = errorMsg;
      } else if (Array.isArray(errorMsg)) {
        errorStr = errorMsg.map((e) => e.msg || JSON.stringify(e)).join("; ");
      } else if (err?.message) {
        errorStr = err.message;
      }
      // 添加API名称信息
      if (err?.apiName) {
        errorStr = `[${err.apiName}] ${errorStr}`;
      }
      setError({
        message: errorStr,
        originalError: err,
        apiName: err?.apiName || err?.config?.url,
        apiIndex: err?.apiIndex,
      });
      setOverallStats(null);
      setTeamPerformance([]);
      setPendingApprovals([]);
      setTopCustomers([]);
      setRecentActivities([]);
      setFunnelData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedPeriod]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  if (loading && !overallStats) {
    return (
      <div className="space-y-6 py-16 text-center text-slate-400">
        <Loader2 className="w-6 h-6 animate-spin mx-auto mb-4 text-primary" />
        <p>正在加载销售总监工作台数据...</p>
      </div>
    );
  }

  // Show error state
  if (error && !overallStats) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="销售总监工作台"
          description="销售战略总览、团队绩效监控"
        />
        <ApiIntegrationError
          error={error}
          apiEndpoint={
            error?.apiName
              ? error.apiName.includes("summary")
                ? "/api/v1/sales/statistics/summary"
                : error.apiName.includes("funnel")
                  ? "/api/v1/sales/statistics/funnel"
                  : error.apiName.includes("getTeam")
                    ? "/api/v1/sales/team"
                    : error.apiName.includes("customerContribution")
                      ? "/api/v1/sales/reports/customer-contribution"
                      : error.apiName.includes("getStatistics")
                        ? "/api/v1/sales/payments/statistics"
                        : error.apiName.includes("list") &&
                            error.apiName.includes("Target")
                          ? "/api/v1/sales/targets"
                          : error?.originalError?.config?.url ||
                            "/api/v1/sales/statistics/summary"
              : error?.originalError?.config?.url ||
                "/api/v1/sales/statistics/summary"
          }
          onRetry={loadDashboard}
        />
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
        title="销售总监工作台"
        description={
          overallStats
            ? `年度目标: ${formatCurrency(overallStats.yearTarget || 0)} | 已完成: ${formatCurrency(overallStats.yearAchieved || 0)} (${(overallStats.yearProgress || 0).toFixed(1)}%)`
            : "销售战略总览、团队绩效监控"
        }
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              销售报表
            </Button>
            <Button className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              团队管理
            </Button>
          </motion.div>
        }
      />

      {/* Key Statistics - 6 column grid */}
      {overallStats && (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6"
        >
          <StatCard
            title="本月签约"
            value={formatCurrency(overallStats.monthlyAchieved || 0)}
            subtitle={`目标: ${formatCurrency(overallStats.monthlyTarget || 0)}`}
            trend={15.2}
            icon={DollarSign}
            color="text-amber-400"
            bg="bg-amber-500/10"
          />
          <StatCard
            title="完成率"
            value={`${overallStats.achievementRate || 0}%`}
            subtitle="本月目标达成"
            icon={Target}
            color="text-emerald-400"
            bg="bg-emerald-500/10"
          />
          <StatCard
            title="活跃客户"
            value={overallStats.totalCustomers || 0}
            subtitle={`本月新增 ${overallStats.newCustomersThisMonth || 0}`}
            trend={8.5}
            icon={Building2}
            color="text-blue-400"
            bg="bg-blue-500/10"
          />
          <StatCard
            title="进行中合同"
            value={overallStats.activeContracts || 0}
            subtitle={`待审批 ${overallStats.pendingContracts || 0}`}
            icon={Briefcase}
            color="text-purple-400"
            bg="bg-purple-500/10"
          />
          <StatCard
            title="待回款"
            value={formatCurrency(overallStats.pendingPayment || 0)}
            subtitle={`逾期 ${formatCurrency(overallStats.overduePayment || 0)}`}
            icon={CreditCard}
            color="text-red-400"
            bg="bg-red-500/10"
          />
          <StatCard
            title="回款率"
            value={`${overallStats.collectionRate || 0}%`}
            subtitle="回款完成率"
            icon={Receipt}
            color="text-cyan-400"
            bg="bg-cyan-500/10"
          />
        </motion.div>
      )}

      {/* Main Content Grid */}
      {overallStats && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Sales Funnel & Team Performance */}
          <div className="lg:col-span-2 space-y-6">
            {/* Sales Funnel */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <BarChart3 className="h-5 w-5 text-blue-400" />
                      销售漏斗分析
                    </CardTitle>
                    <Badge
                      variant="outline"
                      className="bg-blue-500/20 text-blue-400 border-blue-500/30"
                    >
                      {overallStats?.activeOpportunities || 0} 个商机
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  {funnelData ? (
                    <div className="space-y-4">
                      {[
                        {
                          key: "inquiry",
                          label: "询价阶段",
                          color: "bg-blue-500",
                        },
                        {
                          key: "qualification",
                          label: "需求确认",
                          color: "bg-cyan-500",
                        },
                        {
                          key: "proposal",
                          label: "方案报价",
                          color: "bg-amber-500",
                        },
                        {
                          key: "negotiation",
                          label: "商务谈判",
                          color: "bg-orange-500",
                        },
                        {
                          key: "closed",
                          label: "签约成交",
                          color: "bg-emerald-500",
                        },
                      ].map((stage) => {
                        const data = funnelData[stage.key] || {
                          count: 0,
                          amount: 0,
                          conversion: 0,
                        };
                        return (
                          <div key={stage.key} className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                              <div className="flex items-center gap-2">
                                <div
                                  className={cn(
                                    "w-2 h-2 rounded-full",
                                    stage.color,
                                  )}
                                />
                                <span className="text-slate-300">
                                  {stage.label}
                                </span>
                                <Badge
                                  variant="outline"
                                  className="text-xs bg-slate-700/40"
                                >
                                  {data.count} 个
                                </Badge>
                              </div>
                              <div className="flex items-center gap-3">
                                <span className="text-slate-400 text-xs">
                                  转化率:{" "}
                                  {data.conversion?.toFixed?.(1) ??
                                    data.conversion}
                                  %
                                </span>
                                <span className="text-white font-medium">
                                  {formatCurrency(data.amount || 0)}
                                </span>
                              </div>
                            </div>
                            <Progress
                              value={Number(data.conversion) || 0}
                              className="h-2 bg-slate-700/50"
                            />
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-slate-500">
                      <p>暂无漏斗数据</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Users className="h-5 w-5 text-purple-400" />
                      团队业绩排行
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
                  <div className="space-y-4">
                    {teamPerformance.map((member, index) => (
                      <div
                        key={member.id}
                        className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div
                              className={cn(
                                "w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm",
                                index === 0 &&
                                  "bg-gradient-to-br from-amber-500 to-orange-500",
                                index === 1 &&
                                  "bg-gradient-to-br from-blue-500 to-cyan-500",
                                index === 2 &&
                                  "bg-gradient-to-br from-slate-500 to-gray-600",
                                index === 3 &&
                                  "bg-gradient-to-br from-purple-500 to-pink-500",
                              )}
                            >
                              {index + 1}
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-white">
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
                                {member.activeProjects} 个项目 ·{" "}
                                {member.newCustomers} 个新客户
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-lg font-bold text-white">
                              {formatCurrency(member.monthlyAchieved)}
                            </div>
                            <div className="text-xs text-slate-400">
                              目标: {formatCurrency(member.monthlyTarget)}
                            </div>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-400">完成率</span>
                            <span
                              className={cn(
                                "font-medium",
                                member.achievementRate >= 90
                                  ? "text-emerald-400"
                                  : member.achievementRate >= 70
                                    ? "text-amber-400"
                                    : "text-red-400",
                              )}
                            >
                              {member.achievementRate}%
                            </span>
                          </div>
                          <Progress
                            value={member.achievementRate}
                            className="h-1.5 bg-slate-700/50"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Right Column - Pending Approvals & Top Customers */}
          <div className="space-y-6">
            {/* Pending Approvals */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <AlertTriangle className="h-5 w-5 text-amber-400" />
                      待审批事项
                    </CardTitle>
                    <Badge
                      variant="outline"
                      className="bg-amber-500/20 text-amber-400 border-amber-500/30"
                    >
                      {pendingApprovals.length}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {pendingApprovals.map((item) => (
                    <div
                      key={item.id}
                      className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge
                              variant="outline"
                              className={cn(
                                "text-xs",
                                item.type === "contract" &&
                                  "bg-blue-500/20 text-blue-400 border-blue-500/30",
                                item.type === "quotation" &&
                                  "bg-purple-500/20 text-purple-400 border-purple-500/30",
                                item.type === "discount" &&
                                  "bg-red-500/20 text-red-400 border-red-500/30",
                              )}
                            >
                              {item.type === "contract"
                                ? "合同"
                                : item.type === "quotation"
                                  ? "报价"
                                  : "优惠"}
                            </Badge>
                            {item.priority === "high" && (
                              <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                                紧急
                              </Badge>
                            )}
                          </div>
                          <p className="font-medium text-white text-sm">
                            {item.title}
                          </p>
                          <p className="text-xs text-slate-400 mt-1">
                            {item.customer}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between text-xs mt-2">
                        <span className="text-slate-400">
                          {item.submitter} ·{" "}
                          {formatTimelineLabel(item.submitTime)}
                        </span>
                        <span className="font-medium text-amber-400">
                          {formatCurrency(item.amount)}
                        </span>
                      </div>
                    </div>
                  ))}
                  <Button variant="outline" className="w-full mt-3">
                    查看全部审批
                  </Button>
                </CardContent>
              </Card>
            </motion.div>

            {/* Top Customers */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Award className="h-5 w-5 text-amber-400" />
                      重点客户
                    </CardTitle>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs text-primary"
                    >
                      全部 <ChevronRight className="w-3 h-3 ml-1" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {topCustomers.length > 0 ? (
                    topCustomers.map((customer) => (
                      <div
                        key={customer.id}
                        className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div>
                            <p className="font-medium text-white text-sm">
                              {customer.name}
                            </p>
                            <p className="text-xs text-slate-500 mt-1">
                              合同数 {customer.projectCount || 0}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm text-emerald-400 font-semibold">
                              {formatCurrency(customer.totalAmount || 0)}
                            </p>
                            <p className="text-xs text-slate-500">贡献金额</p>
                          </div>
                        </div>
                        <div className="text-xs text-slate-400">
                          最近贡献:{" "}
                          {formatCurrency(
                            customer.thisYear || customer.totalAmount || 0,
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-slate-500">
                      <p>暂无重点客户数据</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      )}

      {/* Year Progress */}
      {overallStats && (
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Activity className="h-5 w-5 text-cyan-400" />
                年度销售目标进度
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400">年度目标</p>
                    <p className="text-2xl font-bold text-white mt-1">
                      {formatCurrency(overallStats.yearTarget || 0)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-slate-400">已完成</p>
                    <p className="text-2xl font-bold text-emerald-400 mt-1">
                      {formatCurrency(overallStats.yearAchieved || 0)}
                    </p>
                  </div>
                </div>
                <Progress
                  value={overallStats.yearProgress || 0}
                  className="h-3 bg-slate-700/50"
                />
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">
                    完成率: {(overallStats.yearProgress || 0).toFixed(1)}%
                  </span>
                  <span className="text-slate-400">
                    剩余:{" "}
                    {formatCurrency(
                      (overallStats.yearTarget || 0) -
                        (overallStats.yearAchieved || 0),
                    )}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {recentActivities.length > 0 && (
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Clock className="h-5 w-5 text-blue-400" />
                关键活动动态
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentActivities.map((activity) => (
                  <div
                    key={activity.id}
                    className="flex items-center justify-between border border-slate-700/40 rounded-lg p-3 bg-slate-800/40"
                  >
                    <div>
                      <p className="text-sm text-white font-medium">
                        {activity.action}
                      </p>
                      <p className="text-xs text-slate-400 mt-1">
                        {activity.target}
                      </p>
                    </div>
                    <div className="text-right">
                      <Badge
                        variant="outline"
                        className="text-xs bg-slate-700/50 border-slate-600"
                      >
                        {formatTimelineLabel(activity.timestamp)}
                      </Badge>
                      <p className="text-xs text-slate-500 mt-1">
                        {activity.operator}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}
