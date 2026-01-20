/**
 * Sales Manager Workstation - Department-level sales management dashboard
 * Features: Team performance, Department metrics, Approval workflow, Customer management
 * Core Functions: Team management, Performance monitoring, Contract approval, Customer relationship
 */

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { BarChart3, Users } from "lucide-react";
import { PageHeader } from "../components/layout";
import { Button } from "../components/ui";
import { formatCurrency } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import {
  salesStatisticsApi,
  salesTeamApi,
  salesTargetApi,
  salesReportApi,
  contractApi,
  paymentPlanApi,
  paymentApi
} from "../services/api";
import { ApiIntegrationError } from "../components/ui";

import {
  KeyStatisticsGrid,
  TeamInsightsCard,
  SalesFunnelCard,
  TeamPerformanceCard,
  PendingApprovalsCard,
  TopCustomersCard,
  PaymentScheduleCard,
  YearProgressCard
} from "../components/sales-manager-workstation";

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
  status: (plan.status || "PENDING").toLowerCase()
});

const normalizeTeamMemberData = (member = {}) => {
  const followStats = member.follow_up_stats || member.followUpStats || {};
  const leadStats = member.lead_quality_stats || member.leadQualityStats || {};
  const opportunityStats =
    member.opportunity_stats || member.opportunityStats || {};
  const monthlyTarget = Number(member.monthly_target || 0);
  const monthlyAchieved = Number(
    member.monthly_actual ?? member.contract_amount ?? 0
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
    leadStats.modeling_rate ??
    (totalLeads ? (modeledLeads / totalLeads) * 100 : 0);
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
      opportunityStats.opportunity_count || member.opportunity_count || 0
    ),
    followUpStats: {
      call: Number(followStats.CALL || 0),
      email: Number(followStats.EMAIL || 0),
      visit: Number(followStats.VISIT || 0),
      meeting: Number(followStats.MEETING || 0),
      other: Number(followStats.OTHER || 0)
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
          : avgCompletenessValue
      )
    },
    pipelineAmount: Number(opportunityStats.pipeline_amount || 0),
    avgEstMargin: Number(opportunityStats.avg_est_margin || 0)
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
        completenessCount: 0
      },
      pipeline: {
        amount: 0,
        opportunityCount: 0,
        marginSum: 0,
        marginCount: 0
      }
    }
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
          ).toFixed(1)
        )
      : 0;
  const avgMargin =
    totals.pipeline.marginCount > 0
      ? Number(
          (totals.pipeline.marginSum / totals.pipeline.marginCount).toFixed(1)
        )
      : 0;

  return {
    followUps: {
      total: followTotal,
      call: totals.follow.call,
      visit: totals.follow.visit,
      meeting: totals.follow.meeting,
      email: totals.follow.email
    },
    leadQuality: {
      totalLeads: totals.leads.total,
      conversionRate,
      modelingRate,
      avgCompleteness
    },
    pipeline: {
      pipelineAmount: totals.pipeline.amount,
      avgMargin,
      opportunityCount: totals.pipeline.opportunityCount
    }
  };
};

export default function SalesManagerWorkstation() {
  const [selectedPeriod, _setSelectedPeriod] = useState("month");
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
        paymentStatsRes
      ] = await Promise.all([
        salesStatisticsApi
          .getDepartmentStatistics({
            start_date: toISODate(start),
            end_date: toISODate(end)
          })
          .catch(() => ({ data: {} })),
        salesStatisticsApi
          .getDepartmentStatistics({
            start_date: toISODate(new Date(start.getFullYear(), 0, 1)),
            end_date: toISODate(end)
          })
          .catch(() => ({ data: {} })),
        salesTargetApi
          .list({
            target_scope: "DEPARTMENT",
            target_period: "MONTHLY",
            period_value: `${start.getFullYear()}-${String(
              start.getMonth() + 1
            ).padStart(2, "0")}`
          })
          .catch(() => ({ data: { items: [] } })),
        salesTargetApi
          .list({
            target_scope: "DEPARTMENT",
            target_period: "YEARLY",
            period_value: String(start.getFullYear())
          })
          .catch(() => ({ data: { items: [] } })),
        salesTeamApi
          .getTeam({
            start_date: toISODate(start),
            end_date: toISODate(end)
          })
          .catch(() => ({ data: { team_members: [] } })),
        salesStatisticsApi
          .getFunnelStatistics({
            start_date: toISODate(start),
            end_date: toISODate(end)
          })
          .catch(() => ({ data: {} })),
        contractApi
          .list({
            page: 1,
            page_size: 100,
            approval_status: "PENDING"
          })
          .catch(() => ({ data: { items: [] } })),
        salesReportApi
          .getCustomerContribution({
            start_date: toISODate(start),
            end_date: toISODate(end)
          })
          .catch(() => ({ data: {} })),
        paymentPlanApi
          .list({
            page: 1,
            page_size: 100,
            planned_date_start: toISODate(start),
            planned_date_end: toISODate(end)
          })
          .catch(() => ({ data: { items: [] } })),
        paymentApi
          .getStatistics({
            start_date: toISODate(start),
            end_date: toISODate(end)
          })
          .catch(() => ({ data: {} }))
      ]);

      const funnelPayload = extractData(funnelRes);
      const teamPayload =
        teamRes?.data?.data || teamRes?.data || extractData(teamRes) || {};
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
          0
        ),
        won: funnelPayload.contracts || 0
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
          Number(contract.contract_amount || 0) > 300000 ? "high" : "medium"
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
        totalAmount: item.total_amount || 0
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
        0
      );
      const newCustomers = normalizedTeam.reduce(
        (sum, member) => sum + (member.newCustomers || 0),
        0
      );
      const overallOpportunities = summaryData?.total_opportunities || 0;
      const teamOpportunityCount = normalizedTeam.reduce(
        (sum, member) => sum + (member.opportunityCount || 0),
        0
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
        yearProgress: Number(yearProgress.toFixed(1))
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
      <PageHeader
        title="销售经理工作台"
        description={
          deptStats
            ? `部门目标: ${formatCurrency(
                deptStats.monthlyTarget || 0
              )} | 已完成: ${formatCurrency(deptStats.monthlyAchieved || 0)} (${
                deptStats.achievementRate || 0
              }%)`
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

      <KeyStatisticsGrid deptStats={deptStats} />

      {teamInsights && <TeamInsightsCard teamInsights={teamInsights} />}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <SalesFunnelCard deptStats={deptStats} salesFunnel={salesFunnel} />
          <TeamPerformanceCard teamMembers={teamMembers} />
        </div>

        <div className="space-y-6">
          <PendingApprovalsCard pendingApprovals={pendingApprovals} />
          <TopCustomersCard topCustomers={topCustomers} />
          <PaymentScheduleCard payments={payments} />
        </div>
      </div>

      {deptStats && <YearProgressCard deptStats={deptStats} />}
    </motion.div>
  );
}
