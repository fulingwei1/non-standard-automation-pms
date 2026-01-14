/**
 * Sales Manager Workstation - Department-level sales management dashboard
 * Features: Team performance, Department metrics, Approval workflow, Customer management
 * Core Functions: Team management, Performance monitoring, Contract approval, Customer relationship
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
  ChevronRight,
  Phone,
  Mail,
  Flame,
  Zap,
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
import { cn, formatCurrency } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import {
  SalesFunnel,
  CustomerCard,
  PaymentTimeline,
} from "../components/sales";
import {
  salesStatisticsApi,
  salesTeamApi,
  salesTargetApi,
  salesReportApi,
  contractApi,
  paymentPlanApi,
  paymentApi,
} from "../services/api";
import { ApiIntegrationError } from "../components/ui";

const toISODate = (value) => value.toISOString().split("T")[0];

const getRangeForPeriod = (period) => {
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

const transformPlanToPayment = (plan) => ({
  id: plan.id,
  type: (plan.payment_type || "progress").toLowerCase(),
  projectName: plan.project_name || plan.contract_name || "收款计划",
  amount: Number(plan.planned_amount || plan.amount || 0),
  dueDate: plan.planned_date || plan.due_date,
  paidDate: plan.actual_date || plan.paid_date,
  status: (plan.status || "PENDING").toLowerCase(),
});

const formatTimelineLabel = (value) => {
  if (!value) return "刚刚";
  try {
    return new Date(value).toLocaleString("zh-CN", { hour12: false });
  } catch (err) {
    return value;
  }
};

// Mock data - 已移除，使用真实API
/* const mockDeptStats = {
  monthlyTarget: 2000000,
  monthlyAchieved: 1680000,
  achievementRate: 84,
  yearTarget: 24000000,
  yearAchieved: 16800000,
  yearProgress: 70,
  teamSize: 8,
  activeContracts: 12,
  pendingApprovals: 3,
  totalCustomers: 68,
  newCustomersThisMonth: 5,
  activeOpportunities: 18,
  hotOpportunities: 7,
  pendingPayment: 850000,
  overduePayment: 120000,
  collectionRate: 88.5,
} */

/* const mockTeamMembers = [
  {
    id: 1,
    name: '张销售',
    role: '销售工程师',
    monthlyTarget: 300000,
    monthlyAchieved: 285000,
    achievementRate: 95,
    activeProjects: 5,
    newCustomers: 2,
    status: 'excellent',
  },
  {
    id: 2,
    name: '李销售',
    role: '销售工程师',
    monthlyTarget: 300000,
    monthlyAchieved: 245000,
    achievementRate: 81.7,
    activeProjects: 4,
    newCustomers: 1,
    status: 'good',
  },
  {
    id: 3,
    name: '王销售',
    role: '销售工程师',
    monthlyTarget: 300000,
    monthlyAchieved: 198000,
    achievementRate: 66,
    activeProjects: 3,
    newCustomers: 0,
    status: 'warning',
  },
  {
    id: 4,
    name: '陈销售',
    role: '销售工程师',
    monthlyTarget: 300000,
    monthlyAchieved: 320000,
    achievementRate: 106.7,
    activeProjects: 6,
    newCustomers: 2,
    status: 'excellent',
  },
] */

/* const mockSalesFunnel = {
  inquiry: { count: 45, amount: 5600000, conversion: 100 },
  qualification: { count: 32, amount: 4200000, conversion: 71.1 },
  proposal: { count: 20, amount: 3200000, conversion: 62.5 },
  negotiation: { count: 12, amount: 2100000, conversion: 60 },
  closed: { count: 7, amount: 1680000, conversion: 58.3 },
} */

// Type config for approvals
const typeConfig = {
  contract: {
    label: "合同审批",
    textColor: "text-blue-400",
    bgColor: "bg-blue-500/20",
  },
  opportunity: {
    label: "商机审批",
    textColor: "text-emerald-400",
    bgColor: "bg-emerald-500/20",
  },
  payment: {
    label: "回款审批",
    textColor: "text-amber-400",
    bgColor: "bg-amber-500/20",
  },
};

const priorityConfig = {
  high: { label: "紧急", color: "text-red-400" },
  medium: { label: "普通", color: "text-amber-400" },
  low: { label: "低", color: "text-slate-400" },
};

const normalizeTeamMemberData = (member = {}) => {
  const followStats = member.follow_up_stats || member.followUpStats || {};
  const leadStats = member.lead_quality_stats || member.leadQualityStats || {};
  const opportunityStats =
    member.opportunity_stats || member.opportunityStats || {};
  const monthlyTarget = Number(member.monthly_target || 0);
  const monthlyAchieved = Number(
    member.monthly_actual ?? member.contract_amount ?? 0,
  );
  const completionRate =
    monthlyTarget > 0
      ? (monthlyAchieved / monthlyTarget) * 100
      : Number(member.monthly_completion_rate || 0);
  const totalLeads = Number(leadStats.total_leads ?? member.lead_count ?? 0);
  const convertedLeads = Number(leadStats.converted_leads || 0);
  const modeledLeads = Number(leadStats.modeled_leads || 0);
  const conversionRate =
    leadStats.conversion_rate ??
    (totalLeads ? (convertedLeads / totalLeads) * 100 : 0);
  const modelingRate =
    leadStats.modeling_rate ?? (totalLeads ? (modeledLeads / totalLeads) * 100 : 0);
  const avgCompletenessValue =
    leadStats.avg_completeness ?? leadStats.avgCompleteness ?? 0;

  return {
    id: member.user_id,
    name: member.user_name || member.username || "未命名成员",
    role: member.role || member.role_name || "销售工程师",
    monthlyTarget,
    monthlyAchieved,
    achievementRate: Number((completionRate || 0).toFixed(1)),
    activeProjects: Number(member.contract_count || 0),
    newCustomers: Number(member.new_customers || 0),
    customerTotal: Number(member.customer_total || 0),
    opportunityCount: Number(
      opportunityStats.opportunity_count || member.opportunity_count || 0,
    ),
    followUpStats: {
      call: Number(followStats.CALL || 0),
      email: Number(followStats.EMAIL || 0),
      visit: Number(followStats.VISIT || 0),
      meeting: Number(followStats.MEETING || 0),
      other: Number(followStats.OTHER || 0),
    },
    leadQuality: {
      totalLeads,
      convertedLeads,
      modeledLeads,
      conversionRate: Number((conversionRate || 0).toFixed(1)),
      modelingRate: Number((modelingRate || 0).toFixed(1)),
      avgCompleteness: Number(
        avgCompletenessValue.toFixed
          ? avgCompletenessValue.toFixed(1)
          : avgCompletenessValue,
      ),
    },
    pipelineAmount: Number(opportunityStats.pipeline_amount || 0),
    avgEstMargin: Number(opportunityStats.avg_est_margin || 0),
  };
};

const calculateTeamInsights = (members = []) => {
  if (!members.length) return null;

  const totals = members.reduce(
    (acc, member) => {
      const follow = member.followUpStats || {};
      acc.follow.call += follow.call || 0;
      acc.follow.email += follow.email || 0;
      acc.follow.visit += follow.visit || 0;
      acc.follow.meeting += follow.meeting || 0;
      acc.follow.other += follow.other || 0;

      const lead = member.leadQuality || {};
      acc.leads.total += lead.totalLeads || 0;
      acc.leads.converted += lead.convertedLeads || 0;
      acc.leads.modeled += lead.modeledLeads || 0;
      if (lead.avgCompleteness !== undefined) {
        acc.leads.completenessSum += Number(lead.avgCompleteness) || 0;
        acc.leads.completenessCount += 1;
      }

      acc.pipeline.amount += member.pipelineAmount || 0;
      acc.pipeline.opportunityCount += member.opportunityCount || 0;
      if (member.avgEstMargin) {
        acc.pipeline.marginSum += member.avgEstMargin;
        acc.pipeline.marginCount += 1;
      }

      return acc;
    },
    {
      follow: { call: 0, email: 0, visit: 0, meeting: 0, other: 0 },
      leads: {
        total: 0,
        converted: 0,
        modeled: 0,
        completenessSum: 0,
        completenessCount: 0,
      },
      pipeline: { amount: 0, opportunityCount: 0, marginSum: 0, marginCount: 0 },
    },
  );

  const followTotal =
    totals.follow.call +
    totals.follow.email +
    totals.follow.visit +
    totals.follow.meeting +
    totals.follow.other;
  const conversionRate =
    totals.leads.total > 0
      ? Number(((totals.leads.converted / totals.leads.total) * 100).toFixed(1))
      : 0;
  const modelingRate =
    totals.leads.total > 0
      ? Number(((totals.leads.modeled / totals.leads.total) * 100).toFixed(1))
      : 0;
  const avgCompleteness =
    totals.leads.completenessCount > 0
      ? Number(
          (
            totals.leads.completenessSum / totals.leads.completenessCount
          ).toFixed(1),
        )
      : 0;
  const avgMargin =
    totals.pipeline.marginCount > 0
      ? Number(
          (totals.pipeline.marginSum / totals.pipeline.marginCount).toFixed(1),
        )
      : 0;

  return {
    followUps: {
      total: followTotal,
      call: totals.follow.call,
      visit: totals.follow.visit,
      meeting: totals.follow.meeting,
      email: totals.follow.email,
    },
    leadQuality: {
      totalLeads: totals.leads.total,
      conversionRate,
      modelingRate,
      avgCompleteness,
    },
    pipeline: {
      pipelineAmount: totals.pipeline.amount,
      avgMargin,
      opportunityCount: totals.pipeline.opportunityCount,
    },
  };
};

const StatCard = ({ title, value, subtitle, trend, icon: Icon, color, bg }) => {
  const [isHovered, setIsHovered] = useState(false);
  return (
    <motion.div
      variants={fadeIn}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
    >
      <Card
        className={cn(
          "transition-all duration-300",
          isHovered && "scale-105",
          bg,
          "border-slate-700/50",
        )}
      >
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-xs text-slate-400 mb-1">{title}</p>
              <p className={cn("text-xl font-bold text-white", color)}>
                {value}
              </p>
              <p className="text-xs text-slate-400 mt-1">{subtitle}</p>
              {trend !== undefined && (
                <div
                  className={cn(
                    "flex items-center text-xs mt-1",
                    trend > 0 ? "text-emerald-400" : "text-red-400",
                  )}
                >
                  {trend > 0 ? (
                    <ArrowUpRight className="w-3 h-3 mr-1" />
                  ) : (
                    <ArrowDownRight className="w-3 h-3 mr-1" />
                  )}
                  {Math.abs(trend)}%
                </div>
              )}
            </div>
            <div className={cn("p-2 rounded-lg", bg)}>
              <Icon className={cn("w-5 h-5", color)} />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default function SalesManagerWorkstation() {
  const [selectedPeriod, setSelectedPeriod] = useState("month");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deptStats, setDeptStats] = useState(null);
  const [teamMembers, setTeamMembers] = useState([]);
  const [teamInsights, setTeamInsights] = useState(null);
  const [salesFunnel, setSalesFunnel] = useState({});
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [topCustomers, setTopCustomers] = useState([]);
  const [payments, setPayments] = useState([]);

  const extractData = (res) => res?.data || {};

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const { start, end } = getRangeForPeriod(selectedPeriod);

      // Parallel API calls for better performance
      const [
        summaryRes,
        yearSummaryRes,
        targetRes,
        yearTargetRes,
        teamRes,
        funnelRes,
        approvalsRes,
        customersRes,
        plansRes,
        paymentStatsRes,
      ] = await Promise.all([
        salesStatisticsApi
          .getDepartmentStatistics({
            start_date: toISODate(start),
            end_date: toISODate(end),
          })
          .catch(() => ({ data: {} })),
        salesStatisticsApi
          .getDepartmentStatistics({
            start_date: toISODate(new Date(start.getFullYear(), 0, 1)),
            end_date: toISODate(end),
          })
          .catch(() => ({ data: {} })),
        salesTargetApi
          .list({
            target_scope: "DEPARTMENT",
            target_period: "MONTHLY",
            period_value: `${start.getFullYear()}-${String(start.getMonth() + 1).padStart(2, "0")}`,
          })
          .catch(() => ({ data: { items: [] } })),
        salesTargetApi
          .list({
            target_scope: "DEPARTMENT",
            target_period: "YEARLY",
            period_value: String(start.getFullYear()),
          })
          .catch(() => ({ data: { items: [] } })),
        salesTeamApi
          .getTeam({
            start_date: toISODate(start),
            end_date: toISODate(end),
          })
          .catch(() => ({ data: { team_members: [] } })),
        salesStatisticsApi
          .getFunnelStatistics({
            start_date: toISODate(start),
            end_date: toISODate(end),
          })
          .catch(() => ({ data: {} })),
        contractApi
          .list({
            page: 1,
            page_size: 100,
            approval_status: "PENDING",
          })
          .catch(() => ({ data: { items: [] } })),
        salesReportApi
          .getCustomerContribution({
            start_date: toISODate(start),
            end_date: toISODate(end),
          })
          .catch(() => ({ data: {} })),
        paymentPlanApi
          .list({
            page: 1,
            page_size: 100,
            planned_date_start: toISODate(start),
            planned_date_end: toISODate(end),
          })
          .catch(() => ({ data: { items: [] } })),
        paymentApi
          .getStatistics({
            start_date: toISODate(start),
            end_date: toISODate(end),
          })
          .catch(() => ({ data: {} })),
      ]);

      const funnelPayload = extractData(funnelRes);
      const teamPayload =
        teamRes?.data?.data ||
        teamRes?.data ||
        extractData(teamRes) ||
        {};
      const teamRaw =
        teamPayload.team_members ||
        teamPayload.items ||
        (Array.isArray(teamPayload) ? teamPayload : []);
      const normalizedTeam = teamRaw.map(normalizeTeamMemberData);
      const approvals = approvalsRes?.data?.items || approvalsRes?.data || [];
      const customerContribution = extractData(customersRes)?.customers || [];
      const planItems = plansRes?.data?.items || plansRes?.data || [];
      const summaryData = extractData(summaryRes);
      const paymentSummary = extractData(paymentStatsRes)?.summary || {};
      const targetItem = targetRes?.data?.items?.[0];
      const yearSummaryData = extractData(yearSummaryRes);
      const yearTargetItem = yearTargetRes?.data?.items?.[0];

      setSalesFunnel({
        lead: funnelPayload.leads || 0,
        contact: funnelPayload.opportunities || 0,
        quote: funnelPayload.quotes || 0,
        negotiate: Math.max(
          (funnelPayload.opportunities || 0) - (funnelPayload.contracts || 0),
          0,
        ),
        won: funnelPayload.contracts || 0,
      });

      setTeamMembers(normalizedTeam);
      setTeamInsights(calculateTeamInsights(normalizedTeam));

      const approvalsTransformed = approvals.map((contract) => ({
        id: contract.id,
        type: "contract",
        title: contract.contract_code || contract.contract_name || "合同审批",
        customer: contract.customer_name || "未命名客户",
        amount: Number(contract.contract_amount || 0),
        submitter: contract.owner_name || "系统",
        submitTime: contract.created_at,
        priority:
          Number(contract.contract_amount || 0) > 300000 ? "high" : "medium",
      }));
      setPendingApprovals(approvalsTransformed);

      const customersMapped = customerContribution.map((item) => ({
        id: item.customer_id || item.customer_name,
        name: item.customer_name || "未命名客户",
        shortName: item.customer_name || "客户",
        grade: "A",
        status: "active",
        industry: item.industry || "未分类",
        location: "",
        lastContact: "",
        opportunityCount: item.contract_count || 0,
        totalAmount: item.total_amount || 0,
      }));
      setTopCustomers(customersMapped);
      setPayments(planItems.map(transformPlanToPayment));

      const monthlyTarget =
        targetItem?.target_value || summaryData?.monthly_target || 0;
      const monthlyAchieved = summaryData?.total_contract_amount || 0;
      const achievementRate =
        monthlyTarget > 0 ? (monthlyAchieved / monthlyTarget) * 100 : 0;
      const totalCustomers = normalizedTeam.reduce(
        (sum, member) => sum + (member.customerTotal || 0),
        0,
      );
      const newCustomers = normalizedTeam.reduce(
        (sum, member) => sum + (member.newCustomers || 0),
        0,
      );
      const overallOpportunities = summaryData?.total_opportunities || 0;
      const teamOpportunityCount = normalizedTeam.reduce(
        (sum, member) => sum + (member.opportunityCount || 0),
        0,
      );

      const yearTargetValue =
        yearTargetItem?.target_value ||
        yearSummaryData?.year_target ||
        monthlyTarget * 12;
      const yearAchieved =
        yearSummaryData?.total_contract_amount || monthlyAchieved;
      const yearProgress =
        yearTargetValue > 0 ? (yearAchieved / yearTargetValue) * 100 : 0;

      setDeptStats({
        monthlyTarget,
        monthlyAchieved,
        achievementRate: Number(achievementRate.toFixed(1)),
        teamSize: normalizedTeam.length,
        activeContracts: summaryData?.signed_contracts || 0,
        pendingApprovals: approvalsTransformed.length,
        totalCustomers,
        newCustomersThisMonth: newCustomers,
        activeOpportunities: overallOpportunities,
        hotOpportunities: teamOpportunityCount,
        pendingPayment: paymentSummary.total_unpaid || 0,
        overduePayment: paymentSummary.total_overdue || 0,
        collectionRate: paymentSummary.collection_rate || 0,
        yearTarget: yearTargetValue,
        yearAchieved,
        yearProgress: Number(yearProgress.toFixed(1)),
      });
    } catch (err) {
      console.error("Failed to load sales manager dashboard:", err);
      setError(err);
      setDeptStats(null);
      setTeamMembers([]);
      setTeamInsights(null);
      setSalesFunnel({});
      setPendingApprovals([]);
      setTopCustomers([]);
      setPayments([]);
    } finally {
      setLoading(false);
    }
  }, [selectedPeriod]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader title="销售经理工作台" description="部门级销售管理仪表板" />
        <div className="text-center py-16 text-slate-400">加载中...</div>
      </div>
    );
  }

  if (error && !deptStats) {
    return (
      <div className="space-y-6">
        <PageHeader title="销售经理工作台" description="部门级销售管理仪表板" />
        <ApiIntegrationError
          error={error}
          apiEndpoint="/api/v1/sales/statistics/department"
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
        title="销售经理工作台"
        description={
          deptStats
            ? `部门目标: ${formatCurrency(deptStats.monthlyTarget || 0)} | 已完成: ${formatCurrency(deptStats.monthlyAchieved || 0)} (${deptStats.achievementRate || 0}%)`
            : "部门级销售管理仪表板"
        }
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              团队报表
            </Button>
            <Button className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              团队管理
            </Button>
          </motion.div>
        }
      />

      {/* Key Statistics */}
      <motion.div
        variants={staggerContainer}
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6"
      >
        {deptStats && (
          <>
            <StatCard
              title="本月签约"
              value={formatCurrency(deptStats.monthlyAchieved || 0)}
              subtitle={`目标: ${formatCurrency(deptStats.monthlyTarget || 0)}`}
              trend={12.5}
              icon={DollarSign}
              color="text-amber-400"
              bg="bg-amber-500/10"
            />
            <StatCard
              title="完成率"
              value={`${deptStats.achievementRate || 0}%`}
              subtitle="本月目标达成"
              icon={Target}
              color="text-emerald-400"
              bg="bg-emerald-500/10"
            />
            <StatCard
              title="团队规模"
              value={deptStats?.teamSize || 0}
              subtitle={`活跃成员 ${deptStats?.teamSize || 0}`}
              icon={Users}
              color="text-blue-400"
              bg="bg-blue-500/10"
            />
            <StatCard
              title="活跃客户"
              value={deptStats?.totalCustomers || 0}
              subtitle={`本月新增 ${deptStats?.newCustomersThisMonth || 0}`}
              trend={6.2}
              icon={Building2}
              color="text-purple-400"
              bg="bg-purple-500/10"
            />
            <StatCard
              title="待回款"
              value={formatCurrency(deptStats?.pendingPayment || 0)}
              subtitle={`逾期 ${formatCurrency(deptStats?.overduePayment || 0)}`}
              icon={CreditCard}
              color="text-red-400"
              bg="bg-red-500/10"
            />
            <StatCard
              title="待审批"
              value={deptStats?.pendingApprovals || 0}
              subtitle="项待处理"
              icon={AlertTriangle}
              color="text-amber-400"
              bg="bg-amber-500/10"
            />
          </>
        )}
      </motion.div>

      {teamInsights && (
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base text-white">
                <Activity className="h-5 w-5 text-cyan-400" />
                团队行为洞察
              </CardTitle>
              <p className="text-sm text-slate-400">
                跟进动作 · 线索质量 · 管道健康
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-slate-300">
                <div className="rounded-lg border border-slate-700/60 bg-slate-900/40 p-4">
                  <p className="text-xs text-slate-400 mb-2">跟进行为</p>
                  <p className="text-2xl font-semibold text-white">
                    {teamInsights.followUps.total} 次
                  </p>
                  <div className="mt-2 space-y-1 text-xs">
                    <p>电话沟通：{teamInsights.followUps.call}</p>
                    <p>拜访次数：{teamInsights.followUps.visit}</p>
                    <p>
                      会议/邮件：
                      {teamInsights.followUps.meeting + teamInsights.followUps.email}
                    </p>
                  </div>
                </div>
                <div className="rounded-lg border border-slate-700/60 bg-slate-900/40 p-4">
                  <p className="text-xs text-slate-400 mb-2">线索质量</p>
                  <p className="text-2xl font-semibold text-white">
                    {teamInsights.leadQuality.totalLeads} 个线索
                  </p>
                  <div className="mt-2 space-y-1 text-xs">
                    <p>线索成功率：{teamInsights.leadQuality.conversionRate}%</p>
                    <p>建模覆盖率：{teamInsights.leadQuality.modelingRate}%</p>
                    <p>
                      信息完整度：{teamInsights.leadQuality.avgCompleteness} 分
                    </p>
                  </div>
                </div>
                <div className="rounded-lg border border-slate-700/60 bg-slate-900/40 p-4">
                  <p className="text-xs text-slate-400 mb-2">销售管道</p>
                  <p className="text-2xl font-semibold text-white">
                    {formatCurrency(teamInsights.pipeline.pipelineAmount || 0)}
                  </p>
                  <div className="mt-2 space-y-1 text-xs">
                    <p>
                      平均毛利率：{teamInsights.pipeline.avgMargin || 0}%
                    </p>
                    <p>
                      在谈商机：
                      {teamInsights.pipeline.opportunityCount} 个
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Main Content Grid */}
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
                    {deptStats?.activeOpportunities || 0} 个商机
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                {Object.keys(salesFunnel).length > 0 ? (
                  <SalesFunnel data={salesFunnel} />
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <p>暂无销售漏斗数据</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Team Performance */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Users className="h-5 w-5 text-purple-400" />
                    团队成员业绩
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
                {teamMembers.length > 0 ? (
                  <div className="space-y-4">
                    {teamMembers.map((member, index) => (
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
                                  {member.name || "N/A"}
                                </span>
                                <Badge
                                  variant="outline"
                                  className="text-xs bg-slate-700/40"
                                >
                                  {member.role || "N/A"}
                                </Badge>
                              </div>
                              <div className="text-xs text-slate-400 mt-1">
                                {member.activeProjects || 0} 个项目 ·{" "}
                                {member.newCustomers || 0} 个新客户
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-lg font-bold text-white">
                              {formatCurrency(
                                member.monthlyAchieved || 0,
                              )}
                            </div>
                            <div className="text-xs text-slate-400">
                              目标: {formatCurrency(member.monthlyTarget || 0)}
                            </div>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-400">完成率</span>
                            <span
                              className={cn(
                                "font-medium",
                                (member.achievementRate || 0) >= 90
                                  ? "text-emerald-400"
                                  : (member.achievementRate || 0) >= 70
                                    ? "text-amber-400"
                                    : "text-red-400",
                              )}
                            >
                              {member.achievementRate || 0}%
                            </span>
                          </div>
                          <Progress
                            value={member.achievementRate || 0}
                            className="h-1.5 bg-slate-700/50"
                          />
                          <div className="mt-3 grid grid-cols-2 gap-2 text-[11px] text-slate-400">
                            <div>电话：{member.followUpStats?.call || 0}</div>
                            <div>拜访：{member.followUpStats?.visit || 0}</div>
                            <div>
                              会议/邮件：
                              {(member.followUpStats?.meeting || 0) +
                                (member.followUpStats?.email || 0)}
                            </div>
                            <div>
                              线索成功率：
                              {member.leadQuality?.conversionRate || 0}%
                            </div>
                            <div>
                              建模覆盖率：
                              {member.leadQuality?.modelingRate || 0}%
                            </div>
                            <div>
                              信息完整度：
                              {member.leadQuality?.avgCompleteness || 0} 分
                            </div>
                            <div>
                              在谈金额：
                              {formatCurrency(member.pipelineAmount || 0)}
                            </div>
                            <div>
                              平均毛利率：{member.avgEstMargin || 0}%
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <p>团队成员数据需要从API获取</p>
                  </div>
                )}
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
                {pendingApprovals.length > 0 ? (
                  pendingApprovals.map((item) => {
                    const typeInfo = typeConfig[item.type];
                    const priorityInfo = priorityConfig[item.priority];
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
                                className={cn("text-xs", typeInfo.textColor)}
                              >
                                {typeInfo.label}
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
                    );
                  })
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <p>暂无待审批事项</p>
                  </div>
                )}
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
                    <CustomerCard
                      key={customer.id}
                      customer={customer}
                      compact
                      onClick={(c) => {
                        // Handle customer click if needed
                      }}
                    />
                  ))
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <p>暂无重点客户数据</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Payment Schedule */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Receipt className="h-5 w-5 text-emerald-400" />
                    近期回款计划
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs text-primary"
                  >
                    全部回款 <ChevronRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {payments.length > 0 ? (
                  <PaymentTimeline payments={payments} compact />
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <p>暂无回款计划</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>

      {/* Year Progress */}
      {deptStats && (
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
                      {formatCurrency(deptStats.yearTarget || 0)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-slate-400">已完成</p>
                    <p className="text-2xl font-bold text-emerald-400 mt-1">
                      {formatCurrency(deptStats.yearAchieved || 0)}
                    </p>
                  </div>
                </div>
                <Progress
                  value={deptStats.yearProgress || 0}
                  className="h-3 bg-slate-700/50"
                />
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">
                    完成率: {deptStats.yearProgress || 0}%
                  </span>
                  <span className="text-slate-400">
                    剩余:{" "}
                    {formatCurrency(
                      (deptStats.yearTarget || 0) -
                        (deptStats.yearAchieved || 0),
                    )}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}
