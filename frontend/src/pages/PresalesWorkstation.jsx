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
    path: "/solutions",
    color: "from-violet-500 to-purple-600"
  },
  {
    name: "新建调研",
    icon: ClipboardList,
    path: "/requirement-survey",
    color: "from-emerald-500 to-teal-600"
  },
  {
    name: "上传文档",
    icon: Upload,
    path: "#",
    color: "from-blue-500 to-cyan-600"
  },
  {
    name: "知识库",
    icon: BookOpen,
    path: "/knowledge-base",
    color: "from-amber-500 to-orange-600"
  }
];

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
      SOLUTION_DESIGN: "方案设计",
      COST_ESTIMATE: "成本核算",
      COST_SUPPORT: "成本支持",
      TECHNICAL_EXCHANGE: "技术交流",
      REQUIREMENT_RESEARCH: "需求调研",
      TENDER_SUPPORT: "投标支持",
      SOLUTION_REVIEW: "方案评审",
      FEASIBILITY_ASSESSMENT: "可行性评估"
    };
    return typeMap[backendType] || backendType;
  };

  const mapSolutionStatus = (backendStatus) => {
    const statusMap = {
      DRAFT: "设计中",
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

      const ticketsResponse = await presaleApi.tickets.list({
        page: 1,
        page_size: 50,
        status: "PENDING,ACCEPTED,IN_PROGRESS"
      });
      const tickets = ticketsResponse.data?.items || ticketsResponse.data || [];

      const transformedTasks = await Promise.all(
        tickets.map(async (ticket) => {
          let solutionId = null;
          try {
            const solutionsResponse = await presaleApi.solutions.list({
              ticket_id: ticket.id,
              page: 1,
              page_size: 1
            });
            const solutions =
            solutionsResponse.data?.items || solutionsResponse.data || [];
            if (solutions.length > 0) {
              solutionId = solutions[0].id;
            }
          } catch (_err) {
            solutionId = null;
          }
          return {
            id: ticket.id,
            title: ticket.title,
            type: mapTicketType(ticket.ticket_type),
            typeColor: getTypeColor(mapTicketType(ticket.ticket_type)),
            source: ticket.applicant_name ?
            `销售：${ticket.applicant_name}` :
            "内部流程",
            deadline: ticket.deadline || ticket.expected_date || "",
            priority: ticket.urgency?.toLowerCase() || "medium",
            customer: ticket.customer_name || "",
            ticketId: ticket.id,
            opportunityId: ticket.opportunity_id,
            biddingId: ticket.project_id,
            solutionId,
            requestedBy: ticket.applicant_name,
            requestedAt: ticket.apply_time
          };
        })
      );

      setTodoTasks(transformedTasks);

      const solutionsResponse = await presaleApi.solutions.list({
        page: 1,
        page_size: 20,
        status: "DRAFT,REVIEWING,SUBMITTED"
      });
      const solutions =
      solutionsResponse.data?.items || solutionsResponse.data || [];

      const transformedSolutions = solutions.map((solution) => ({
        id: solution.id,
        name: solution.name,
        customer: solution.customer_id ? "客户" : "",
        version: solution.version || "V1.0",
        status: mapSolutionStatus(solution.status),
        statusColor:
        solution.status === "REVIEWING" ?
        "bg-amber-500" :
        solution.status === "APPROVED" ?
        "bg-emerald-500" :
        "bg-blue-500",
        progress:
        solution.status === "APPROVED" ?
        100 :
        solution.status === "REVIEWING" ?
        85 :
        60,
        deadline: solution.estimated_duration ? "" : "",
        amount: solution.estimated_cost || solution.suggested_price || 0,
        deviceType: solution.test_type || solution.solution_type || ""
      }));

      setOngoingSolutions(transformedSolutions);

      const tendersResponse = await presaleApi.tenders.list({
        page: 1,
        page_size: 10
      });
      const tenders = tendersResponse.data?.items || tendersResponse.data || [];

      const transformedTenders = tenders.map((tender) => ({
        id: tender.id,
        name: tender.tender_name || tender.project_name || "",
        customer: tender.customer_name || "",
        deadline: tender.submission_deadline || "",
        status: tender.status || "PREPARING",
        statusColor:
        tender.status === "SUBMITTED" ? "bg-emerald-500" : "bg-amber-500",
        amount: tender.budget || 0,
        progress: tender.status === "SUBMITTED" ? 100 : 60
      }));

      setRecentTenders(transformedTenders);

      const opportunitiesResponse = await opportunityApi.list({
        page: 1,
        page_size: 10,
        stage: "QUALIFICATION,PROPOSAL"
      });
      const opportunities =
      opportunitiesResponse.data?.items || opportunitiesResponse.data || [];

      const transformedOpportunities = opportunities.map((opp) => ({
        id: opp.id,
        name: opp.name,
        customer: opp.customer_name || "",
        stage: opp.stage || "",
        amount: opp.estimated_value || 0,
        probability: opp.probability || 0,
        expectedDate: opp.expected_close_date || ""
      }));

      setRelatedOpportunities(transformedOpportunities);

      const pendingTickets = tickets.filter(
        (t) => t.status === "PENDING"
      ).length;
      const reviewingSolutions = solutions.filter(
        (s) => s.status === "REVIEWING"
      ).length;
      const totalEstimatedValue = transformedSolutions.reduce(
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
        value: solutions.length.toString(),
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
        tenders.filter((t) => {
          const deadline = new Date(t.submission_deadline);
          const now = new Date();
          return (
            deadline >= now &&
            deadline <= new Date(now.getFullYear(), now.getMonth() + 1, 0));

        }).length}`,

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
        statsData.map((s) => ({ ...s, value: "0", subtitle: "暂无数据" }))
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
        const solutions =
        solutionsResponse.data?.items || solutionsResponse.data || [];

        if (solutions.length > 0) {
          await presaleApi.solutions.update(solutions[0].id, {
            estimated_cost: costData.totalAmount * YUAN_TO_CENTS,
            suggested_price: costData.suggestedPrice * YUAN_TO_CENTS
          });
        } else {
          const ticketResponse = await presaleApi.tickets.get(
            selectedCostTask.ticketId
          );
          const ticket = ticketResponse.data;

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
          progress: 100,
          notes: `成本估算已完成，总成本：¥${costData.totalAmount}万，建议报价：¥${costData.suggestedPrice}万`
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
        await presaleApi.tickets.update(selectedFeasibilityTask.ticketId, {
          description: `${selectedFeasibilityTask.description || ""}\n\n可行性评估结果：\n综合评分：${assessmentData.overallScore.toFixed(1)}分\n可行性：${assessmentData.feasibility === "feasible" ? "可行" : assessmentData.feasibility === "conditional" ? "有条件可行" : "不可行"}\n评估建议：${assessmentData.recommendation}\n风险分析：${assessmentData.riskAnalysis}\n技术说明：${assessmentData.technicalNotes}`
        });

        await presaleApi.tickets.updateProgress(
          selectedFeasibilityTask.ticketId,
          {
            progress: 100,
            notes: `可行性评估已完成，综合评分：${assessmentData.overallScore.toFixed(1)}分`
          }
        );
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
