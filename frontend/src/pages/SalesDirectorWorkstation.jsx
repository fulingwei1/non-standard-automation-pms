/**
 * Sales Director Workstation - Executive dashboard for sales directors
 * Features: Strategic overview, Team performance, Sales analytics, Revenue monitoring
 * Core Functions: Sales strategy, Team management, Performance monitoring, Contract approval
 */

import { useState, useEffect, useCallback, useMemo } from "react";
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

const RANKING_PRIMARY_KEYS = [
  "contract_amount",
  "acceptance_amount",
  "collection_amount",
];

const RANKING_METRIC_LIBRARY = [
  {
    value: "contract_amount",
    label: "签单额（合同金额）",
    description: "统计周期内签订的合同金额",
    defaultWeight: 0.4,
    isPrimary: true,
  },
  {
    value: "acceptance_amount",
    label: "验收金额",
    description: "已审批/已开票金额，代表验收进度",
    defaultWeight: 0.2,
    isPrimary: true,
  },
  {
    value: "collection_amount",
    label: "回款金额",
    description: "周期内到账的回款金额",
    defaultWeight: 0.2,
    isPrimary: true,
  },
  {
    value: "opportunity_count",
    label: "商机提交数",
    description: "新增并推进的商机数量",
    defaultWeight: 0.05,
  },
  {
    value: "lead_conversion_rate",
    label: "线索成功率",
    description: "线索转商机/签单成功率",
    defaultWeight: 0.05,
  },
  {
    value: "modeling_rate",
    label: "建模覆盖率",
    description: "重点线索是否完成方案建模",
    defaultWeight: 0.05,
  },
  {
    value: "info_completeness",
    label: "商务信息完整度",
    description: "商机/客户信息补充完整情况",
    defaultWeight: 0.05,
  },
  {
    value: "follow_up_total",
    label: "跟进行为次数",
    description: "电话、会议、邮件等总跟进次数",
    defaultWeight: 0.05,
  },
  {
    value: "follow_up_visit",
    label: "拜访次数",
    description: "出差/上门拜访次数",
    defaultWeight: 0.05,
  },
  {
    value: "pipeline_amount",
    label: "管道金额",
    description: "当前在跟进的商机金额总和",
    defaultWeight: 0.05,
  },
  {
    value: "avg_est_margin",
    label: "平均预估毛利率",
    description: "商机的平均预估毛利率",
    defaultWeight: 0.05,
  },
];

const isPrimaryMetric = (metric = {}) =>
  metric.is_primary ||
  RANKING_PRIMARY_KEYS.includes(metric.data_source) ||
  RANKING_PRIMARY_KEYS.includes(metric.key);

const calculateRankingValidation = (metrics = []) => {
  if (!metrics.length) {
    return {
      totalWeight: 0,
      primaryWeight: 0,
      errors: ["至少需要配置一条指标"],
    };
  }
  const errors = [];
  let totalWeight = 0;
  let primaryWeight = 0;
  const seenKeys = new Set();

  metrics.forEach((metric) => {
    const key = metric.key || metric.data_source;
    if (!key) {
      errors.push("存在缺少唯一 key 的指标");
      return;
    }
    if (seenKeys.has(key)) {
      errors.push(`指标 ${metric.label || key} 的 key 重复`);
    } else {
      seenKeys.add(key);
    }
    const weight = Number(metric.weight || 0);
    if (Number.isNaN(weight) || weight <= 0) {
      errors.push(`指标 ${metric.label || key} 的权重要大于0`);
    }
    totalWeight += weight;
    const isPrimary =
      metric.is_primary ||
      RANKING_PRIMARY_KEYS.includes(metric.data_source) ||
      RANKING_PRIMARY_KEYS.includes(key);
    if (isPrimary) {
      primaryWeight += weight;
    }
  });

  if (Math.abs(totalWeight - 1) > 0.0001) {
    errors.push("所有指标权重之和必须等于100%");
  }
  if (Math.abs(primaryWeight - 0.8) > 0.0001) {
    errors.push("签单额+验收金额+回款金额需占80%的权重");
  }

  return { totalWeight, primaryWeight, errors };
};

const formatConfigTimestamp = (value) => {
  if (!value) return "尚未配置";
  const time = new Date(value);
  if (Number.isNaN(time.getTime())) return value;
  return time.toLocaleString("zh-CN", { hour12: false });
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

const normalizeTeamMember = (member = {}) => {
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
    monthlyAchieved,
    monthlyTarget,
    achievementRate: Number((completionRate || 0).toFixed(1)),
    activeProjects: Number(member.contract_count || 0),
    newCustomers: Number(member.new_customers || 0),
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
  const [teamInsights, setTeamInsights] = useState(null);
  const [rankingConfig, setRankingConfig] = useState(null);
  const [configDraft, setConfigDraft] = useState([]);
  const [configLoading, setConfigLoading] = useState(false);
  const [configSaving, setConfigSaving] = useState(false);
  const [configFormError, setConfigFormError] = useState("");
  const [configSuccessMessage, setConfigSuccessMessage] = useState("");
  const [isEditingConfig, setIsEditingConfig] = useState(false);
  const [metricToAdd, setMetricToAdd] = useState("");
  const [configLoadError, setConfigLoadError] = useState("");
  const metricValidation = useMemo(
    () => calculateRankingValidation(configDraft),
    [configDraft],
  );
  const displayRankingMetrics = useMemo(() => {
    const targets = isEditingConfig
      ? configDraft
      : rankingConfig?.metrics || [];
    return [...targets].sort(
      (a, b) => Number(b.weight || 0) - Number(a.weight || 0),
    );
  }, [configDraft, rankingConfig, isEditingConfig]);
  const metricSelectOptions = useMemo(() => {
    const base = [...RANKING_METRIC_LIBRARY];
    (configDraft || []).forEach((metric) => {
      const value = metric.data_source || metric.key;
      if (!value) return;
      if (!base.some((option) => option.value === value)) {
        base.push({
          value,
          label: metric.label || value,
          description: metric.description || "自定义指标",
        });
      }
    });
    return base;
  }, [configDraft]);
  const availableMetricOptions = useMemo(() => {
    const usedKeys = new Set(
      (configDraft || []).map((metric) => metric.data_source || metric.key),
    );
    return RANKING_METRIC_LIBRARY.filter(
      (metric) => !usedKeys.has(metric.value),
    );
  }, [configDraft]);

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
      const teamPayload =
        teamRes?.data?.data || teamRes?.data || teamRes || {};
      const teamMembersRaw =
        teamPayload.team_members ||
        teamPayload.items ||
        (Array.isArray(teamPayload) ? teamPayload : []);
      const approvals = approvalsRes?.data?.items || approvalsRes?.data || [];
      const customerContribution = extractData(customersRes)?.customers || [];
      const paymentSummary = extractData(paymentStatsRes)?.summary || {};
      const opportunities =
        opportunitiesRes?.data?.items || opportunitiesRes?.data || [];
      const invoices = invoicesRes?.data?.items || invoicesRes?.data || [];
      const monthTarget = monthTargetsRes?.data?.items?.[0];
      const yearTarget = yearTargetsRes?.data?.items?.[0];

      const normalizedTeamAll = teamMembersRaw.map(normalizeTeamMember);
      const normalizedTeam = [...normalizedTeamAll]
        .sort((a, b) => (b.monthlyAchieved || 0) - (a.monthlyAchieved || 0))
        .slice(0, 4);
      setTeamPerformance(normalizedTeam);
      setTeamInsights(calculateTeamInsights(normalizedTeamAll));

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
      setTeamInsights(null);
      setPendingApprovals([]);
      setTopCustomers([]);
      setRecentActivities([]);
      setFunnelData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedPeriod]);

  const fetchRankingConfig = useCallback(async () => {
    try {
      setConfigLoading(true);
      setConfigLoadError("");
      setConfigFormError("");
      setConfigSuccessMessage("");
      const res = await salesTeamApi.getRankingConfig();
      const payload = res.data?.data || res.data || {};
      const normalizedMetrics = (payload.metrics || []).map((metric) => {
        const dataSource = metric.data_source || metric.key;
        return {
          key: metric.key || dataSource,
          label: metric.label || metric.key || dataSource,
          weight: Number(metric.weight || 0),
          data_source: dataSource,
          description: metric.description,
          is_primary:
            metric.is_primary ||
            RANKING_PRIMARY_KEYS.includes(metric.key) ||
            RANKING_PRIMARY_KEYS.includes(dataSource),
        };
      });
      const normalizedConfig = {
        ...payload,
        metrics: normalizedMetrics,
      };
      setRankingConfig(normalizedConfig);
      setConfigDraft(normalizedMetrics);
      setIsEditingConfig(false);
    } catch (err) {
      console.error("Failed to fetch ranking config:", err);
      setConfigLoadError(
        err?.response?.data?.detail || "加载销售人员评价模型失败，请稍后重试。",
      );
    } finally {
      setConfigLoading(false);
    }
  }, []);

  const handleStartEditConfig = () => {
    setIsEditingConfig(true);
    setConfigDraft(rankingConfig?.metrics || []);
    setConfigFormError("");
    setConfigSuccessMessage("");
  };

  const handleCancelEditConfig = () => {
    setIsEditingConfig(false);
    setConfigDraft(rankingConfig?.metrics || []);
    setMetricToAdd("");
    setConfigFormError("");
  };

  const handleMetricLabelChange = (index, value) => {
    setConfigDraft((prev) =>
      prev.map((metric, idx) =>
        idx === index ? { ...metric, label: value } : metric,
      ),
    );
  };

  const handleMetricWeightChange = (index, percentValue) => {
    setConfigDraft((prev) =>
      prev.map((metric, idx) => {
        if (idx !== index) return metric;
        const numericPercent = Number(percentValue);
        if (Number.isNaN(numericPercent)) {
          return { ...metric, weight: 0 };
        }
        const normalized = Math.min(Math.max(numericPercent, 0), 100) / 100;
        return { ...metric, weight: Number(normalized.toFixed(4)) };
      }),
    );
  };

  const handleMetricDataSourceChange = (index, value) => {
    if (!value) return;
    setConfigDraft((prev) =>
      prev.map((metric, idx) => {
        if (idx !== index) return metric;
        const option =
          metricSelectOptions.find((item) => item.value === value) ||
          RANKING_METRIC_LIBRARY.find((item) => item.value === value);
        const shouldResetLabel =
          !metric.label ||
          metric.label === metric.key ||
          metric.label === metric.data_source;
        const nextKey =
          metric.key && metric.key !== metric.data_source
            ? metric.key
            : value;
        return {
          ...metric,
          data_source: value,
          key: nextKey,
          label: shouldResetLabel
            ? option?.label || metric.label || value
            : metric.label,
          description: option?.description || metric.description,
          is_primary:
            option?.isPrimary || RANKING_PRIMARY_KEYS.includes(value),
        };
      }),
    );
  };

  const handleRemoveMetric = (index) => {
    setConfigDraft((prev) =>
      prev.filter((metric, idx) => {
        if (idx !== index) return true;
        return !isPrimaryMetric(metric);
      }),
    );
  };

  const handleAddMetric = () => {
    if (!metricToAdd) return;
    const template = RANKING_METRIC_LIBRARY.find(
      (item) => item.value === metricToAdd,
    );
    if (!template) return;
    setConfigDraft((prev) => [
      ...prev,
      {
        key: template.value,
        label: template.label,
        weight: template.defaultWeight || 0.05,
        data_source: template.value,
        description: template.description,
        is_primary: Boolean(template.isPrimary),
      },
    ]);
    setMetricToAdd("");
  };

  const handleSaveRankingConfig = async () => {
    const validationResult = calculateRankingValidation(configDraft);
    if (validationResult.errors.length > 0) {
      setConfigFormError(validationResult.errors.join("；"));
      return;
    }
    setConfigSaving(true);
    setConfigFormError("");
    try {
      const payload = {
        metrics: (configDraft || []).map((metric) => ({
          key: metric.key || metric.data_source,
          label: metric.label || metric.key || metric.data_source,
          weight: Number(metric.weight || 0),
          data_source: metric.data_source || metric.key,
          description: metric.description,
          is_primary: Boolean(isPrimaryMetric(metric)),
        })),
      };
      const res = await salesTeamApi.updateRankingConfig(payload);
      const responseData = res.data?.data || res.data || payload;
      const normalizedMetrics = (responseData.metrics || payload.metrics).map(
        (metric) => ({
          ...metric,
          is_primary:
            metric.is_primary ||
            RANKING_PRIMARY_KEYS.includes(metric.data_source) ||
            RANKING_PRIMARY_KEYS.includes(metric.key),
        }),
      );
      setRankingConfig({ ...responseData, metrics: normalizedMetrics });
      setConfigDraft(normalizedMetrics);
      setIsEditingConfig(false);
      setConfigSuccessMessage("销售人员评价模型已更新");
      setMetricToAdd("");
    } catch (err) {
      console.error("Failed to update ranking config:", err);
      setConfigFormError(
        err?.response?.data?.detail || "保存失败，请检查权重是否符合要求。",
      );
    } finally {
      setConfigSaving(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    fetchRankingConfig();
  }, [fetchRankingConfig]);

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

      {/* Ranking Config */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/70 to-slate-900/70 border border-slate-700/60">
          <CardHeader>
            <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-base text-white">
                  <Award className="h-5 w-5 text-amber-400" />
                  销售人员评价模型
                </CardTitle>
                <p className="text-xs text-slate-400 mt-1">
                  顶层设定考核指标与权重，确保签单额/验收金额/回款金额占80%
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={fetchRankingConfig}
                  disabled={configLoading}
                >
                  刷新配置
                </Button>
                {isEditingConfig ? (
                  <Button variant="outline" size="sm" onClick={handleCancelEditConfig}>
                    取消
                  </Button>
                ) : (
                  <Button size="sm" onClick={handleStartEditConfig}>
                    调整权重
                  </Button>
                )}
              </div>
            </div>
            <div className="text-xs text-slate-500 mt-2">
              最近更新时间：{formatConfigTimestamp(rankingConfig?.updated_at)}
            </div>
            {configLoadError && (
              <p className="text-xs text-red-400 mt-2">{configLoadError}</p>
            )}
            {!isEditingConfig && configSuccessMessage && (
              <p className="text-xs text-emerald-400 mt-2">
                {configSuccessMessage}
              </p>
            )}
          </CardHeader>
          <CardContent className="space-y-4">
            {configLoading ? (
              <div className="py-8 text-center text-slate-400">
                正在读取最新配置...
              </div>
            ) : !rankingConfig?.metrics?.length ? (
              <div className="py-6 text-sm text-slate-400">
                暂无配置，请点击“调整权重”添加指标。
              </div>
            ) : isEditingConfig ? (
              <div className="space-y-4">
                <div className="overflow-x-auto rounded-lg border border-slate-700/60">
                  <table className="min-w-full divide-y divide-slate-700/70 text-sm">
                    <thead className="bg-slate-800/50">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400">
                          指标名称
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400">
                          数据来源
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400">
                          权重 (%)
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400">
                          属性
                        </th>
                        <th className="px-3 py-2" />
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {configDraft.map((metric, index) => {
                        const percentValue = Number(metric.weight || 0) * 100;
                        const primary = isPrimaryMetric(metric);
                        return (
                          <tr key={`${metric.key}-${metric.data_source}-${index}`}>
                            <td className="px-3 py-3 align-top">
                              <input
                                value={metric.label || ""}
                                onChange={(e) =>
                                  handleMetricLabelChange(index, e.target.value)
                                }
                                className="w-full rounded-md border border-slate-700 bg-slate-900/60 px-2 py-1 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/60"
                              />
                              <p className="mt-1 text-[11px] text-slate-500">
                                {metric.description || "用于展示在排名表中的名称"}
                              </p>
                            </td>
                            <td className="px-3 py-3 align-top">
                              <select
                                value={metric.data_source || metric.key}
                                onChange={(e) =>
                                  handleMetricDataSourceChange(index, e.target.value)
                                }
                                disabled={primary}
                                className={cn(
                                  "w-full rounded-md border px-2 py-1 text-sm bg-slate-900/60 text-white focus:outline-none focus:ring-2 focus:ring-primary/60",
                                  primary
                                    ? "border-slate-700/80 text-slate-500 cursor-not-allowed"
                                    : "border-slate-700",
                                )}
                              >
                                {metricSelectOptions.map((option) => (
                                  <option key={option.value} value={option.value}>
                                    {option.label}
                                  </option>
                                ))}
                              </select>
                              <p className="mt-1 text-[11px] text-slate-500">
                                {primary ? "核心指标不可更改数据来源" : "选择需要考核的数据源字段"}
                              </p>
                            </td>
                            <td className="px-3 py-3 align-top">
                              <div className="flex items-center gap-2">
                                <input
                                  type="number"
                                  min="0"
                                  max="100"
                                  step="1"
                                  value={percentValue.toFixed(0)}
                                  onChange={(e) =>
                                    handleMetricWeightChange(index, e.target.value)
                                  }
                                  className="w-20 rounded-md border border-slate-700 bg-slate-900/60 px-2 py-1 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/60"
                                />
                                <span className="text-xs text-slate-500">%</span>
                              </div>
                            </td>
                            <td className="px-3 py-3 align-top">
                              <Badge
                                variant="outline"
                                className={cn(
                                  "text-xs",
                                  primary
                                    ? "bg-amber-500/20 border-amber-500/40 text-amber-200"
                                    : "bg-slate-700/40 border-slate-600 text-slate-300",
                                )}
                              >
                                {primary ? "核心" : "辅助"}
                              </Badge>
                            </td>
                            <td className="px-3 py-3 align-top text-right">
                              <Button
                                variant="ghost"
                                size="sm"
                                disabled={primary}
                                onClick={() => handleRemoveMetric(index)}
                              >
                                移除
                              </Button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                  <select
                    value={metricToAdd}
                    onChange={(e) => setMetricToAdd(e.target.value)}
                    className="w-full rounded-md border border-slate-700 bg-slate-900/60 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/60 sm:w-64"
                  >
                    <option value="">选择要新增的考核指标</option>
                    {availableMetricOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <Button
                    variant="outline"
                    onClick={handleAddMetric}
                    disabled={!metricToAdd}
                  >
                    新增指标
                  </Button>
                </div>
                <div className="flex flex-wrap gap-4 text-xs text-slate-400">
                  <span>
                    总权重：{(metricValidation.totalWeight * 100).toFixed(1)}%
                  </span>
                  <span>
                    核心指标权重：
                    {(metricValidation.primaryWeight * 100).toFixed(1)}%（需80%）
                  </span>
                </div>
                {configFormError && (
                  <p className="text-xs text-red-400">{configFormError}</p>
                )}
                <div className="flex flex-wrap gap-2">
                  <Button
                    onClick={handleSaveRankingConfig}
                    loading={configSaving}
                    disabled={configSaving}
                  >
                    保存配置
                  </Button>
                  <Button variant="ghost" onClick={handleCancelEditConfig}>
                    取消
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {displayRankingMetrics.map((metric) => (
                    <div
                      key={`${metric.key}-${metric.data_source}`}
                      className="p-3 rounded-lg border border-slate-700/60 bg-slate-900/60"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm text-white">{metric.label}</p>
                          <p className="text-[11px] text-slate-500 mt-1">
                            {metric.description || "——"}
                          </p>
                        </div>
                        <Badge
                          variant="outline"
                          className={cn(
                            "text-xs",
                            isPrimaryMetric(metric)
                              ? "border-amber-500/40 text-amber-200"
                              : "border-slate-600 text-slate-300",
                          )}
                        >
                          {(Number(metric.weight || 0) * 100).toFixed(0)}%
                        </Badge>
                      </div>
                      <Progress
                        value={Number(metric.weight || 0) * 100}
                        className="h-1.5 bg-slate-800 mt-3"
                      />
                    </div>
                  ))}
                </div>
                <p className="text-xs text-slate-500">
                  说明：签单额、验收金额、回款金额三项总权重固定为80%，其余指标用于衡量跟进行为、线索质量与毛利率等表现。
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

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

      {teamInsights && (
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-slate-700/60">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-base text-white">
                  <Activity className="h-5 w-5 text-cyan-400" />
                  全局销售洞察
                </CardTitle>
                <Badge
                  variant="outline"
                  className="bg-slate-800/60 border-slate-700 text-slate-300"
                >
                  {teamInsights.leadQuality.totalLeads} 条线索
                </Badge>
              </div>
              <p className="text-sm text-slate-400">
                汇总团队跟进动作、线索质量与在谈管道，为销售决策提供依据
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-slate-200">
                <div className="rounded-lg border border-slate-700/60 bg-slate-900/40 p-4">
                  <p className="text-xs text-slate-400">团队跟进</p>
                  <p className="text-2xl font-semibold text-white mt-1">
                    {teamInsights.followUps.total} 次
                  </p>
                  <div className="mt-3 space-y-1 text-xs text-slate-400">
                    <p>电话：{teamInsights.followUps.call}</p>
                    <p>拜访：{teamInsights.followUps.visit}</p>
                    <p>
                      会议/邮件：
                      {teamInsights.followUps.meeting + teamInsights.followUps.email}
                    </p>
                  </div>
                </div>
                <div className="rounded-lg border border-slate-700/60 bg-slate-900/40 p-4">
                  <p className="text-xs text-slate-400">线索质量</p>
                  <p className="text-2xl font-semibold text-white mt-1">
                    成功率 {teamInsights.leadQuality.conversionRate}%
                  </p>
                  <div className="mt-3 space-y-1 text-xs text-slate-400">
                    <p>建模覆盖率：{teamInsights.leadQuality.modelingRate}%</p>
                    <p>
                      信息完整度：{teamInsights.leadQuality.avgCompleteness} 分
                    </p>
                  </div>
                </div>
                <div className="rounded-lg border border-slate-700/60 bg-slate-900/40 p-4">
                  <p className="text-xs text-slate-400">销售管道</p>
                  <p className="text-2xl font-semibold text-white mt-1">
                    {formatCurrency(teamInsights.pipeline.pipelineAmount || 0)}
                  </p>
                  <div className="mt-3 space-y-1 text-xs text-slate-400">
                    <p>平均毛利率：{teamInsights.pipeline.avgMargin || 0}%</p>
                    <p>
                      在谈商机：{teamInsights.pipeline.opportunityCount} 个
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
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
                            <div>平均毛利率：{member.avgEstMargin || 0}%</div>
                          </div>
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
