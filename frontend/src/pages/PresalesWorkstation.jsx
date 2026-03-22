/**
 * 售前技术工程师工作台
 * 核心入口页面，展示技术支持任务、方案进度、投标项目等
 */
import { useState, useEffect, useCallback } from "react";
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
import { presaleApi, opportunityApi } from "../services/api";

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
const SOLUTION_CENTER_PATH = "/presales/solutions";

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
    path: "/presales/technical-solutions?tab=surveys",
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

  // 演示数据 - 当 API 不可用时使用
  const getMockData = () => {
    const mockTasks = [
      { id: 1, title: "新能源电池测试方案", type: "方案设计", typeColor: "bg-blue-500", source: "销售：张经理", deadline: "2026-03-15", priority: "high", customer: "宁德时代" },
      { id: 2, title: "汽车电子成本核算", type: "成本核算", typeColor: "bg-amber-500", source: "销售：李总", deadline: "2026-03-12", priority: "medium", customer: "比亚迪" },
      { id: 3, title: "充电桩测试可行性评估", type: "可行性评估", typeColor: "bg-violet-500", source: "内部流程", deadline: "2026-03-18", priority: "low", customer: "特来电" },
    ];
    const mockSolutions = [
      { id: 1, name: "动力电池EOL测试系统", customer: "宁德时代", version: "V2.1", status: "评审中", statusColor: "bg-amber-500", progress: 85, amount: 3800000 },
      { id: 2, name: "BMS测试方案", customer: "比亚迪", version: "V1.0", status: "设计中", statusColor: "bg-blue-500", progress: 60, amount: 2500000 },
    ];
    const mockTenders = [
      { id: 1, name: "新能源汽车测试设备采购", customer: "广汽埃安", deadline: "2026-03-20", status: "准备中", statusColor: "bg-amber-500", amount: 5000000, progress: 60, daysLeft: 11 },
    ];
    const mockOpportunities = [
      { id: 1, name: "储能系统测试项目", customer: "阳光电源", stage: "方案跟进", stageColor: "bg-violet-500/20 text-violet-300", amount: 8000000, winRate: 60, salesPerson: "张经理", expectedDate: "2026-04-30" },
    ];
    return { mockTasks, mockSolutions, mockTenders, mockOpportunities };
  };

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      let tickets = [];
      try {
        const ticketsResponse = await presaleApi.tickets.list({
          page: 1,
          page_size: 50,
          status: "PENDING,ACCEPTED,PROCESSING,REVIEW,IN_PROGRESS"
        });
        tickets = extractItems(ticketsResponse);
      } catch (apiErr) {
        // API 调用失败，使用演示数据
        const { mockTasks, mockSolutions, mockTenders, mockOpportunities } = getMockData();
        setTodoTasks(mockTasks);
        setOngoingSolutions(mockSolutions);
        setRecentTenders(mockTenders);
        setRelatedOpportunities(mockOpportunities);
        setStats(statsData);
        setLoading(false);
        return;
      }

      const solutionsResponse = await presaleApi.solutions.list({
        page: 1,
        page_size: 100
      });
      const allSolutions = extractItems(solutionsResponse);
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
          opportunityId: ticket.opportunity_id,
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

      const tendersResponse = await presaleApi.tenders.list({
        page: 1,
        page_size: 10
      });
      const tenders = extractItems(tendersResponse);

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

      const opportunitiesResponse = await opportunityApi.list({
        page: 1,
        page_size: 10,
        stage: "QUALIFICATION,PROPOSAL"
      });
      const opportunities = extractItems(opportunitiesResponse);

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
      if (selectedCostTask?.solutionId) {
        await presaleApi.solutions.update(selectedCostTask.solutionId, {
          estimated_cost: costData.totalAmount * YUAN_TO_CENTS,
          suggested_price: costData.suggestedPrice * YUAN_TO_CENTS
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
            estimated_cost: costData.totalAmount * YUAN_TO_CENTS,
            suggested_price: costData.suggestedPrice * YUAN_TO_CENTS
          });
        } else {
          const ticketResponse = await presaleApi.tickets.get(
            selectedCostTask.ticketId
          );
          const ticket = ticketResponse.data?.data || ticketResponse.data;

          if (ticket.opportunity_id) {
            await presaleApi.solutions.create({
              name: selectedCostTask.title,
              ticket_id: selectedCostTask.ticketId,
              opportunity_id: ticket.opportunity_id,
              customer_id: ticket.customer_id,
              estimated_cost: costData.totalAmount * YUAN_TO_CENTS,
              suggested_price: costData.suggestedPrice * YUAN_TO_CENTS
            });
          }
        }
      }

      if (selectedCostTask?.ticketId && costData.status === "submitted") {
        await presaleApi.tickets.updateProgress(selectedCostTask.ticketId, {
          progress_note: `成本估算已完成，总成本：¥${costData.totalAmount}万，建议报价：¥${costData.suggestedPrice}万`,
          progress_percent: 100
        });
      }

      await loadData();

      alert("成本估算已提交！");
      setShowCostForm(false);
      setSelectedCostTask(null);
    } catch (err) {
      alert(
        "保存失败：" + (
        err.response?.data?.detail || err.message || "未知错误")
      );
    }
  };

  const handleFeasibilitySave = async (assessmentData) => {
    try {
      if (selectedFeasibilityTask?.ticketId) {
        await presaleApi.tickets.update(selectedFeasibilityTask.ticketId, {
          description: `${selectedFeasibilityTask.description || ""}\n\n可行性评估结果：\n综合评分：${assessmentData.overallScore.toFixed(1)}分\n可行性：${assessmentData.feasibility === "feasible" ? "可行" : assessmentData.feasibility === "conditional" ? "有条件可行" : "不可行"}\n评估建议：${assessmentData.recommendation}\n风险分析：${assessmentData.riskAnalysis}\n技术说明：${assessmentData.technicalNotes}`
        });

        await presaleApi.tickets.updateProgress(
          selectedFeasibilityTask.ticketId,
          {
            progress_note: `可行性评估已完成，综合评分：${assessmentData.overallScore.toFixed(1)}分`,
            progress_percent: 100
          }
        );
      }

      await loadData();

      alert("可行性评估已提交！");
      setShowFeasibilityForm(false);
      setSelectedFeasibilityTask(null);
    } catch (err) {
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
          <TodoTasksCard tasks={todoTasks} onTaskClick={handleCostTaskClick} />
          <OngoingSolutionsCard solutions={ongoingSolutions} />
        </motion.div>

        <motion.div variants={fadeIn} className="space-y-6">
          <QuickActionsCard actions={quickActions} />
          <RecentTendersCard tenders={recentTenders} />
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
