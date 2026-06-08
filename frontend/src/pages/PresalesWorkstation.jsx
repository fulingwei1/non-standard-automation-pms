/**
 * 售前技术工程师工作台
 * 核心入口页面，展示技术支持任务、方案进度、投标项目等
 */
import { useState, useEffect, useCallback, useMemo } from "react";
import { useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ListTodo,
  FileText,
  Target,
  BookOpen,
  Plus,
  Upload,
  Search,
  DollarSign,
  ClipboardList
} from "lucide-react";
import { PageHeader } from "../components/layout";
import { Button } from "../components/ui/button";
import { fadeIn, staggerContainer } from "../lib/animations";
import { presaleApi, presaleWorkbenchApi, technicalAssessmentApi } from "../services/api";

import StatsCards from "../components/presales/workstation/StatsCards";
import TodoTasksCard from "../components/presales/workstation/TodoTasksCard";
import OngoingSolutionsCard from "../components/presales/workstation/OngoingSolutionsCard";
import QuickActionsCard from "../components/presales/workstation/QuickActionsCard";
import RecentTendersCard from "../components/presales/workstation/RecentTendersCard";
import LinkedOpportunitiesCard from "../components/presales/workstation/LinkedOpportunitiesCard";
import CostEstimateDialog from "../components/presales/workstation/CostEstimateDialog";
import FeasibilityAssessmentDialog from "../components/presales/workstation/FeasibilityAssessmentDialog";
import { getTypeColor } from "../components/presales/workstation/utils";

const YUAN_TO_CENTS = 10000;
const SOLUTION_CENTER_PATH = "/presales/technical-solutions?tab=solutions";
const TASK_REVIEW_PATH = "/presales/technical-solutions?tab=reviews";
const SURVEY_CENTER_PATH = "/presales/technical-solutions?tab=surveys";
const BID_CENTER_PATH = "/presales/technical-solutions?tab=bids";

function mergeCurrentSearch(to, currentSearch) {
  if (!currentSearch) {
    return to;
  }

  const [pathname, rawSearch = ""] = to.split("?");
  const nextParams = new URLSearchParams(rawSearch);
  const currentParams = new URLSearchParams(currentSearch);

  currentParams.forEach((value, key) => {
    if (!nextParams.has(key)) {
      nextParams.append(key, value);
    }
  });

  const nextSearch = nextParams.toString();
  return nextSearch ? `${pathname}?${nextSearch}` : pathname;
}

function buildPresaleCenterLink(to, currentSearch) {
  if (!to.startsWith("/presales/technical-solutions")) {
    return to;
  }
  return mergeCurrentSearch(to, currentSearch);
}

function toYuanAmount(amount) {
  const parsed = Number(amount);
  if (!Number.isFinite(parsed)) {
    return 0;
  }
  return Math.round(parsed * YUAN_TO_CENTS);
}

function buildCostBreakdown(costResult) {
  if (costResult?.costData?.cost_breakdown) {
    return costResult.costData.cost_breakdown;
  }

  const costs = costResult?.costs || {};
  return {
    mechanical: toYuanAmount(costs.mechanical?.amount),
    electrical: toYuanAmount(costs.electrical?.amount),
    software: toYuanAmount(costs.software?.amount),
    standard: toYuanAmount(costs.standard?.amount),
    labor: toYuanAmount(costs.labor?.amount),
    other: toYuanAmount(costs.other?.amount),
    notes: costResult?.notes || "",
  };
}

function buildCostSolutionFields(costResult) {
  return {
    estimated_cost: toYuanAmount(costResult?.totalAmount),
    suggested_price: toYuanAmount(costResult?.suggestedPrice),
    cost_breakdown: buildCostBreakdown(costResult),
  };
}

function getAssessmentApplyId(response) {
  return (
    response?.data?.data?.assessment_id ??
    response?.data?.assessment_id ??
    response?.data?.data?.id ??
    response?.data?.id ??
    response?.assessment_id ??
    response?.id ??
    null
  );
}

function scoreToValue(score, highValue, mediumValue, lowValue) {
  const numericScore = Number(score || 0);
  if (numericScore >= 4) {
    return highValue;
  }
  if (numericScore >= 3) {
    return mediumValue;
  }
  return lowValue;
}

function averageScores(scores, keys) {
  const values = keys
    .map((key) => Number(scores?.[key] || 0))
    .filter((value) => Number.isFinite(value) && value > 0);

  if (values.length === 0) {
    return 0;
  }

  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function buildFeasibilityRequirementData(task, assessmentData) {
  const scores = assessmentData?.scores || {};
  const resourceScore = averageScores(scores, [
    "resource_human_resource",
    "resource_material",
    "resource_time",
  ]);
  const marketScore = averageScores(scores, [
    "market_demand",
    "market_customer_value",
    "market_trend",
  ]);

  return {
    source_type: task?.opportunityId ? "OPPORTUNITY" : "LEAD",
    source_id: task?.opportunityId || task?.leadId,
    presale_ticket_id: task?.ticketId,
    project_id: task?.projectId,
    task_title: task?.title,
    customer_name: task?.customer,
    raw_scores: scores,
    overall_score: assessmentData?.overallScore,
    feasibility: assessmentData?.feasibility,
    recommendation: assessmentData?.recommendation || "",
    risk_analysis: assessmentData?.riskAnalysis || "",
    technical_notes: assessmentData?.technicalNotes || "",
    assessed_at: assessmentData?.assessedAt,
    tech_maturity: scoreToValue(scores.technical_tech_maturity, "mature", "medium", "low"),
    process_difficulty: scoreToValue(scores.technical_complexity, "standard", "medium", "high"),
    precision_requirement: scoreToValue(scores.technical_risk, "normal", "high", "extreme"),
    sample_support: scoreToValue(assessmentData?.overallScore / 20, "available", "limited", "none"),
    budget_status: scoreToValue(scores.financial_profitability, "confirmed", "rough", "unknown"),
    price_sensitivity: scoreToValue(scores.financial_cost_control, "low", "medium", "high"),
    gross_margin_safety: scoreToValue(scores.financial_profitability, "safe", "tight", "risk"),
    payment_terms: scoreToValue(scores.financial_payment_risk, "good", "normal", "poor"),
    resource_occupancy: scoreToValue(resourceScore, "available", "tight", "unavailable"),
    has_similar_case: scoreToValue(scores.technical_tech_maturity, "yes", "partial", "no"),
    delivery_feasibility: scoreToValue(scores.resource_time, "feasible", "tight", "risky"),
    delivery_months: scoreToValue(scores.resource_time, 3, 4, 6),
    change_risk: scoreToValue(scores.technical_risk, "low", "medium", "high"),
    customer_nature: scoreToValue(marketScore, "key", "normal", "normal"),
    customer_potential: scoreToValue(scores.market_customer_value, "high", "medium", "low"),
    relationship_depth: scoreToValue(scores.market_demand, "deep", "normal", "new"),
    contact_level: scoreToValue(scores.market_trend, "decision_maker", "influencer", "operator"),
  };
}

const statsData = [
  {
    id: 1,
    title: "本周任务",
    value: "12",
    subtitle: "待处理 5",
    icon: ListTodo,
    color: "text-blue-400",
    bgColor: "bg-blue-400/10",
    trend: "+3"
  },
  {
    id: 2,
    title: "进行中方案",
    value: "8",
    subtitle: "待评审 3",
    icon: FileText,
    color: "text-violet-400",
    bgColor: "bg-violet-400/10",
    trend: "+2"
  },
  {
    id: 3,
    title: "投标项目",
    value: "4",
    subtitle: "本月截止 2",
    icon: Target,
    color: "text-amber-400",
    bgColor: "bg-amber-400/10",
    trend: null
  },
  {
    id: 4,
    title: "预计产出",
    value: "¥386万",
    subtitle: "按方案金额",
    icon: DollarSign,
    color: "text-emerald-400",
    bgColor: "bg-emerald-400/10",
    trend: "+15%"
  }
];

const quickActions = [
  {
    name: "新建方案",
    icon: FileText,
    path: SOLUTION_CENTER_PATH,
    color: "from-violet-500 to-purple-600"
  },
  {
    name: "新建调研",
    icon: ClipboardList,
    path: SURVEY_CENTER_PATH,
    color: "from-emerald-500 to-teal-600"
  },
  {
    name: "上传文档",
    icon: Upload,
    path: "/documents",
    color: "from-blue-500 to-cyan-600"
  },
  {
    name: "知识库",
    icon: BookOpen,
    path: "/knowledge-base",
    color: "from-amber-500 to-orange-600"
  }
];

function extractItems(response) {
  const payload = response?.data ?? response;
  if (Array.isArray(payload)) {
    return payload;
  }
  if (Array.isArray(payload?.items)) {
    return payload.items;
  }
  if (Array.isArray(payload?.data?.items)) {
    return payload.data.items;
  }
  if (Array.isArray(payload?.data)) {
    return payload.data;
  }
  return [];
}

function formatDateLabel(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleDateString("zh-CN");
}

function getDaysLeft(value) {
  if (!value) {
    return null;
  }

  const deadline = new Date(value);
  if (Number.isNaN(deadline.getTime())) {
    return null;
  }

  const now = new Date();
  return Math.ceil((deadline - now) / (1000 * 60 * 60 * 24));
}

function normalizeSolutionStatus(status, reviewStatus) {
  const currentStatus = String(status || "").toUpperCase();
  const currentReviewStatus = String(reviewStatus || "").toUpperCase();

  if (currentStatus === "APPROVED" || currentStatus === "DELIVERED" || currentStatus === "WON") {
    return "APPROVED";
  }
  if (currentStatus === "REJECTED" || currentStatus === "LOST") {
    return "REJECTED";
  }
  if (
    currentStatus === "REVIEW" ||
    currentStatus === "REVIEWING" ||
    currentReviewStatus === "PENDING" ||
    currentReviewStatus === "REVIEWING"
  ) {
    return "REVIEWING";
  }
  if (currentStatus === "SUBMITTED" || currentStatus === "IN_PROGRESS") {
    return "SUBMITTED";
  }
  return "DRAFT";
}

function isOngoingSolution(solution) {
  return ["DRAFT", "REVIEWING", "SUBMITTED"].includes(
    normalizeSolutionStatus(solution?.status, solution?.review_status)
  );
}

function mapOpportunityStage(stage) {
  const stageMap = {
    QUALIFICATION: "资格评估",
    PROPOSAL: "方案跟进",
    QUOTATION: "报价阶段",
    NEGOTIATION: "商务谈判",
  };
  return stageMap[stage] || stage || "待推进";
}

function getOpportunityStageColor(stage) {
  const colorMap = {
    QUALIFICATION: "bg-blue-500/20 text-blue-300",
    PROPOSAL: "bg-violet-500/20 text-violet-300",
    QUOTATION: "bg-amber-500/20 text-amber-300",
    NEGOTIATION: "bg-emerald-500/20 text-emerald-300",
  };
  return colorMap[stage] || "bg-slate-500/20 text-slate-300";
}

function mapTenderStatus(result) {
  const normalizedResult = String(result || "PENDING").toUpperCase();
  const labelMap = {
    PENDING: "准备中",
    WON: "已中标",
    LOST: "未中标",
    CANCELLED: "已取消",
  };
  const colorMap = {
    PENDING: "bg-amber-500",
    WON: "bg-emerald-500",
    LOST: "bg-red-500",
    CANCELLED: "bg-slate-500",
  };

  return {
    key: normalizedResult,
    label: labelMap[normalizedResult] || normalizedResult,
    color: colorMap[normalizedResult] || "bg-slate-500",
  };
}

export default function PresalesWorkstation() {
  const location = useLocation();
  const [_loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(statsData);
  const [todoTasks, setTodoTasks] = useState([]);
  const [ongoingSolutions, setOngoingSolutions] = useState([]);
  const [recentTenders, setRecentTenders] = useState([]);
  const [relatedOpportunities, setRelatedOpportunities] = useState([]);
  const [selectedCostTask, setSelectedCostTask] = useState(null);
  const [showCostForm, setShowCostForm] = useState(false);
  const [selectedFeasibilityTask, setSelectedFeasibilityTask] = useState(null);
  const [showFeasibilityForm, setShowFeasibilityForm] = useState(false);
  const contextualQuickActions = useMemo(
    () =>
      quickActions.map((action) => ({
        ...action,
        path: buildPresaleCenterLink(action.path, location.search),
      })),
    [location.search],
  );
  const taskReviewPath = useMemo(
    () => buildPresaleCenterLink(TASK_REVIEW_PATH, location.search),
    [location.search],
  );
  const solutionCenterPath = useMemo(
    () => buildPresaleCenterLink(SOLUTION_CENTER_PATH, location.search),
    [location.search],
  );
  const bidCenterPath = useMemo(
    () => buildPresaleCenterLink(BID_CENTER_PATH, location.search),
    [location.search],
  );

  const mapTicketType = (backendType) => {
    const typeMap = {
      SOLUTION: "方案设计",
      SOLUTION_DESIGN: "方案设计",
      QUOTATION: "成本核算",
      COST_ESTIMATE: "成本核算",
      COST_SUPPORT: "成本支持",
      MEETING: "技术交流",
      TECHNICAL_EXCHANGE: "技术交流",
      SURVEY: "需求调研",
      REQUIREMENT_RESEARCH: "需求调研",
      TENDER: "投标支持",
      TENDER_SUPPORT: "投标支持",
      CONSULT: "技术交流",
      SOLUTION_REVIEW: "方案评审",
      FEASIBILITY_ASSESSMENT: "可行性评估"
    };
    return typeMap[backendType] || backendType;
  };

  const mapSolutionStatus = (backendStatus) => {
    const statusMap = {
      DRAFT: "设计中",
      REVIEW: "评审中",
      REVIEWING: "评审中",
      APPROVED: "已通过",
      REJECTED: "已驳回",
      SUBMITTED: "已提交"
    };
    return statusMap[backendStatus] || backendStatus;
  };

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const overview = await presaleWorkbenchApi.loadOverview({
        ticketParams: {
          page: 1,
          page_size: 50,
          status: "PENDING,ACCEPTED,PROCESSING,REVIEW,IN_PROGRESS"
        },
        solutionParams: {
          page: 1,
          page_size: 100
        },
        tenderParams: {
          page: 1,
          page_size: 10
        },
        opportunityParams: {
          page: 1,
          page_size: 10,
          stage: "QUALIFICATION,PROPOSAL"
        }
      });
      const tickets = overview.tickets.items;
      const allSolutions = overview.solutions.items;
      const tenders = overview.tenders.items;
      const opportunities = overview.opportunities.items;
      const latestSolutionByTicketId = new Map();

      [...allSolutions]
        .sort((left, right) => {
          const leftTime = new Date(left?.updated_at || left?.created_at || 0).getTime();
          const rightTime = new Date(right?.updated_at || right?.created_at || 0).getTime();
          return rightTime - leftTime;
        })
        .forEach((solution) => {
          if (solution?.ticket_id && !latestSolutionByTicketId.has(solution.ticket_id)) {
            latestSolutionByTicketId.set(solution.ticket_id, solution);
          }
        });

      const transformedTasks = (tickets || []).map((ticket) => {
        const taskType = mapTicketType(ticket.ticket_type);
        const relatedSolution = latestSolutionByTicketId.get(ticket.id);

        return {
          id: ticket.id,
          title: ticket.title,
          type: taskType,
          typeColor: getTypeColor(taskType),
          source: ticket.applicant_name ? `销售：${ticket.applicant_name}` : "内部流程",
          deadline: formatDateLabel(ticket.deadline || ticket.expected_date) || "待排期",
          priority:
            ticket.urgency === "VERY_URGENT" || ticket.urgency === "URGENT"
              ? "high"
              : "medium",
          customer: ticket.customer_name || "待确认客户",
          ticketId: ticket.id,
          leadId: ticket.lead_id,
          opportunityId: ticket.opportunity_id,
          projectId: ticket.project_id,
          biddingId: ticket.project_id,
          solutionId: relatedSolution?.id || null,
          requestedBy: ticket.applicant_name,
          requestedAt: ticket.apply_time,
          description: ticket.description || ""
        };
      });

      setTodoTasks(transformedTasks);

      const activeSolutions = (allSolutions || []).filter(isOngoingSolution);
      const transformedSolutions = activeSolutions.map((solution) => {
        const normalizedStatus = normalizeSolutionStatus(solution.status, solution.review_status);

        return {
        id: solution.id,
        name: solution.name,
        customer:
          solution.customer_name ||
          (solution.customer_id ? `客户 #${solution.customer_id}` : "待关联客户"),
        version: solution.version || "V1.0",
        status: mapSolutionStatus(normalizedStatus),
        statusColor:
        normalizedStatus === "REVIEWING" ?
        "bg-amber-500" :
        normalizedStatus === "APPROVED" ?
        "bg-emerald-500" :
        "bg-blue-500",
        progress:
        normalizedStatus === "APPROVED" ?
        100 :
        normalizedStatus === "REVIEWING" ?
        85 :
        60,
        deadline:
          solution.estimated_duration
            ? `${solution.estimated_duration} 天`
            : formatDateLabel(solution.updated_at || solution.created_at) || "待排期",
        amount: Number(solution.estimated_cost || solution.suggested_price || 0),
        deviceType: solution.test_type || solution.solution_type || "未分类"
      };
      });

      setOngoingSolutions(transformedSolutions);

      const transformedTenders = (tenders || []).map((tender) => {
        const tenderStatus = mapTenderStatus(tender.result);

        return {
          id: tender.id,
          name: tender.tender_name || tender.project_name || "",
          customer: tender.customer_name || "待确认客户",
          deadline: formatDateLabel(tender.deadline) || "待定",
          status: tenderStatus.label,
          statusColor: tenderStatus.color,
          amount: Number(tender.budget_amount || tender.budget || 0),
          progress: tenderStatus.key === "PENDING" ? 60 : 100,
          daysLeft: getDaysLeft(tender.deadline)
        };
      });

      setRecentTenders(transformedTenders);

      const transformedOpportunities = (opportunities || []).map((opp) => ({
        id: opp.id,
        name: opp.opp_name || opp.opportunity_name || opp.name || "未命名商机",
        customer: opp.customer_name || "待确认客户",
        stage: mapOpportunityStage(opp.stage),
        stageColor: getOpportunityStageColor(opp.stage),
        amount: Number(opp.est_amount || opp.estimated_value || 0),
        winRate: opp.probability || 0,
        salesPerson: opp.owner_name || "待分配",
        expectedDate: formatDateLabel(opp.expected_close_date) || "待定"
      }));

      setRelatedOpportunities(transformedOpportunities);

      const pendingTickets = (tickets || []).filter(
        (t) => t.status === "PENDING"
      ).length;
      const reviewingSolutions = (activeSolutions || []).filter(
        (s) => normalizeSolutionStatus(s.status, s.review_status) === "REVIEWING"
      ).length;
      const totalEstimatedValue = (transformedSolutions || []).reduce(
        (sum, s) => sum + (s.amount || 0),
        0
      );

      setStats([
      {
        id: 1,
        title: "本周任务",
        value: tickets.length.toString(),
        subtitle: `待处理 ${pendingTickets}`,
        icon: ListTodo,
        color: "text-blue-400",
        bgColor: "bg-blue-400/10",
        trend: null
      },
      {
        id: 2,
        title: "进行中方案",
        value: activeSolutions.length.toString(),
        subtitle: `待评审 ${reviewingSolutions}`,
        icon: FileText,
        color: "text-violet-400",
        bgColor: "bg-violet-400/10",
        trend: null
      },
      {
        id: 3,
        title: "投标项目",
        value: tenders.length.toString(),
        subtitle: `本月截止 ${
        (transformedTenders || []).filter((t) => t.daysLeft !== null && t.daysLeft >= 0 && t.daysLeft <= 31).length}`,

        icon: Target,
        color: "text-amber-400",
        bgColor: "bg-amber-400/10",
        trend: null
      },
      {
        id: 4,
        title: "预计产出",
        value: `¥${(totalEstimatedValue / 10000).toFixed(0)}万`,
        subtitle: "按方案金额",
        icon: DollarSign,
        color: "text-emerald-400",
        bgColor: "bg-emerald-400/10",
        trend: null
      }]
      );
    } catch (err) {
      console.error("Failed to load presales data:", err);
      setError(err.response?.data?.detail || err.message || "加载数据失败");
      setTodoTasks([]);
      setOngoingSolutions([]);
      setRecentTenders([]);
      setRelatedOpportunities([]);
      setStats(
        (statsData || []).map((s) => ({ ...s, value: "0", subtitle: "暂无数据" }))
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCostTaskClick = (task) => {
    if (task.type === "成本支持" || task.type === "成本核算") {
      setSelectedCostTask(task);
      setShowCostForm(true);
    } else if (task.type === "可行性评估") {
      setSelectedFeasibilityTask(task);
      setShowFeasibilityForm(true);
    }
  };

  const handleCostSave = async (costData) => {
    try {
      const costSolutionFields = buildCostSolutionFields(costData);
      if (selectedCostTask?.solutionId) {
        await presaleApi.solutions.update(selectedCostTask.solutionId, {
          ...costSolutionFields
        });
      } else if (selectedCostTask?.ticketId) {
        const solutionsResponse = await presaleApi.solutions.list({
          ticket_id: selectedCostTask.ticketId,
          page: 1,
          page_size: 1
        });
        const solutions = extractItems(solutionsResponse);

        if (solutions.length > 0) {
          await presaleApi.solutions.update(solutions[0].id, {
            ...costSolutionFields
          });
        } else {
          const ticketResponse = await presaleApi.tickets.get(
            selectedCostTask.ticketId
          );
          const ticket = ticketResponse.data?.data || ticketResponse.data;

          const projectId = ticket.project_id ?? selectedCostTask.biddingId;
          const solutionPayload = {
            name: selectedCostTask.title,
            ticket_id: selectedCostTask.ticketId,
            ...costSolutionFields
          };

          if (ticket.customer_id != null && ticket.customer_id !== "") {
            solutionPayload.customer_id = ticket.customer_id;
          }
          if (ticket.lead_id != null && ticket.lead_id !== "") {
            solutionPayload.lead_id = ticket.lead_id;
          }
          if (ticket.opportunity_id != null && ticket.opportunity_id !== "") {
            solutionPayload.opportunity_id = ticket.opportunity_id;
          }
          if (projectId != null && projectId !== "") {
            solutionPayload.project_id = projectId;
          }

          await presaleApi.solutions.create(solutionPayload);
        }
      }

      if (selectedCostTask?.ticketId && costData.status === "submitted") {
        await presaleApi.tickets.complete(selectedCostTask.ticketId, {
          completion_note: `成本估算已完成，总成本：¥${costData.totalAmount}万，建议报价：¥${costData.suggestedPrice}万`
        });
      }

      await loadData();

      alert("成本估算已提交！");
      setShowCostForm(false);
      setSelectedCostTask(null);
    } catch (err) {
      console.error("Failed to save cost estimation:", err);
      alert(
        "保存失败：" + (
        err.response?.data?.detail || err.message || "未知错误")
      );
    }
  };

  const handleFeasibilitySave = async (assessmentData) => {
    try {
      if (selectedFeasibilityTask?.ticketId) {
        const scoreText = assessmentData.overallScore.toFixed(1);
        const feasibilityText =
          assessmentData.feasibility === "feasible"
            ? "可行"
            : assessmentData.feasibility === "conditional"
              ? "有条件可行"
              : "不可行";
        const recommendation = assessmentData.recommendation || "未填写";
        const riskAnalysis = assessmentData.riskAnalysis || "未填写";
        const technicalNotes = assessmentData.technicalNotes || "未填写";

        const sourcePayload = {
          presale_ticket_id: selectedFeasibilityTask.ticketId,
        };
        const sourceType = selectedFeasibilityTask.opportunityId
          ? "opportunity"
          : selectedFeasibilityTask.leadId
            ? "lead"
            : "";
        const sourceId = selectedFeasibilityTask.opportunityId || selectedFeasibilityTask.leadId;

        if (sourceType && sourceId) {
          const applyResponse =
            sourceType === "opportunity"
              ? await technicalAssessmentApi.applyForOpportunity(sourceId, sourcePayload)
              : await technicalAssessmentApi.applyForLead(sourceId, sourcePayload);
          const assessmentId = getAssessmentApplyId(applyResponse);

          if (!assessmentId) {
            throw new Error("技术评估申请未返回评估ID");
          }

          await technicalAssessmentApi.evaluate(assessmentId, {
            requirement_data: {
              ...buildFeasibilityRequirementData(selectedFeasibilityTask, assessmentData),
              feasibility_result: `综合评分：${scoreText}分；可行性：${feasibilityText}`,
              recommendation,
              risk_analysis: riskAnalysis,
              technical_notes: technicalNotes,
            },
            enable_ai: false,
          });
        } else {
          await presaleApi.tickets.update(selectedFeasibilityTask.ticketId, {
            description: `${selectedFeasibilityTask.description || ""}\n\n可行性评估结果：\n综合评分：${scoreText}分\n可行性：${feasibilityText}\n评估建议：${recommendation}\n风险分析：${riskAnalysis}\n技术说明：${technicalNotes}`
          });

          await presaleApi.tickets.complete(selectedFeasibilityTask.ticketId, {
            completion_note: `可行性评估已完成，综合评分：${scoreText}分，可行性：${feasibilityText}。评估建议：${recommendation}`
          });
        }
      }

      await loadData();

      alert("可行性评估已提交！");
      setShowFeasibilityForm(false);
      setSelectedFeasibilityTask(null);
    } catch (err) {
      console.error("Failed to save feasibility assessment:", err);
      alert(
        "保存失败：" + (
        err.response?.data?.detail || err.message || "未知错误")
      );
    }
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      <PageHeader
        title="售前工作台"
        description="技术方案设计 · 客户需求对接 · 投标技术支持"
        actions={
        <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Search className="w-4 h-4" />
              搜索方案
            </Button>
            <Button className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              新建方案
            </Button>
        </motion.div>
        } />


      {error &&
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
          {error}
      </div>
      }
      
      <StatsCards stats={stats} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div variants={fadeIn} className="lg:col-span-2 space-y-6">
          <TodoTasksCard
            tasks={todoTasks}
            onTaskClick={handleCostTaskClick}
            allTasksPath={taskReviewPath}
          />
          <OngoingSolutionsCard
            solutions={ongoingSolutions}
            solutionCenterPath={solutionCenterPath}
          />
        </motion.div>

        <motion.div variants={fadeIn} className="space-y-6">
          <QuickActionsCard actions={contextualQuickActions} />
          <RecentTendersCard tenders={recentTenders} allTendersPath={bidCenterPath} />
          <LinkedOpportunitiesCard opportunities={relatedOpportunities} />
        </motion.div>
      </div>

      <CostEstimateDialog
        isOpen={showCostForm}
        task={selectedCostTask}
        onClose={() => setShowCostForm(false)}
        onSave={handleCostSave}
      />

      <FeasibilityAssessmentDialog
        isOpen={showFeasibilityForm}
        task={selectedFeasibilityTask}
        onClose={() => setShowFeasibilityForm(false)}
        onSave={handleFeasibilitySave}
      />
    </motion.div>);

}
