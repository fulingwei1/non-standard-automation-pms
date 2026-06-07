/**
 * 需求调研管理
 * 管理客户需求调研记录、现场勘察、问题跟踪
 */
import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ClipboardList,
  Search,
  Plus,
  Calendar,
  Users,
  CheckCircle,
  AlertTriangle,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
} from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { presaleApi } from "../../services/api";
import { surveyMethods, surveyStatuses } from "./constants";
import { mapTicketTypeToMethod, mapTicketStatus } from "./utils";
import SurveyCard from "./SurveyCard";
import SurveyDetailPanel from "./SurveyDetailPanel";

function parseContextId(value) {
  if (!value) {
    return null;
  }

  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

export default function RequirementSurvey({ embedded = false }) {
  const [searchParams] = useSearchParams();
  const contextTicketId = searchParams.get("ticket_id") || "";
  const contextOpportunityId = searchParams.get("opportunity_id") || "";
  const contextProjectId = searchParams.get("project_id") || "";
  const contextTicketIdNumber = parseContextId(contextTicketId);
  const contextOpportunityIdNumber = parseContextId(contextOpportunityId);
  const contextProjectIdNumber = parseContextId(contextProjectId);
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [selectedMethod, setSelectedMethod] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSurvey, setSelectedSurvey] = useState(null);
  const [surveys, setSurveys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load surveys from API
  const loadSurveys = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page: 1,
        page_size: 100,
        ticket_type: "REQUIREMENT_RESEARCH,TECHNICAL_EXCHANGE,SITE_VISIT",
      };

      if (selectedStatus !== "all") {
        const statusMap = {
          scheduled: "PENDING,ACCEPTED",
          in_progress: "IN_PROGRESS",
          completed: "COMPLETED",
          cancelled: "CANCELLED",
        };
        params.status = statusMap[selectedStatus] || selectedStatus;
      }

      if (searchTerm) {
        params.keyword = searchTerm;
      }
      if (contextOpportunityIdNumber) {
        params.opportunity_id = contextOpportunityId;
      }
      if (contextTicketIdNumber) {
        params.ticket_id = contextTicketId;
      }
      if (contextProjectIdNumber) {
        params.project_id = contextProjectId;
      }

      const response = await presaleApi.tickets.list(params);
      const ticketsData = response.data?.items || response.data?.items || response.data || [];

      // Transform tickets to surveys
      const transformedSurveys = (ticketsData || []).map((ticket) => {
        const method = mapTicketTypeToMethod(ticket.ticket_type);
        const methodConfig =
          (surveyMethods || []).find((m) => m.id === method) || surveyMethods[0];
        return {
          id: ticket.id,
          code: ticket.ticket_no || `SUR-${ticket.id}`,
          customer: ticket.customer_name || "",
          customerId: ticket.customer_id,
          contactPerson: ticket.applicant_name || "",
          contactPhone: "",
          method,
          methodName: methodConfig.name,
          status: mapTicketStatus(ticket.status),
          scheduledDate: ticket.expected_date || ticket.apply_time || "",
          completedDate: ticket.complete_time || null,
          location: ticket.description || "",
          engineer: ticket.assignee_name || ticket.owner_name || "",
          salesPerson: ticket.applicant_name || "",
          opportunity: ticket.opportunity_name || "",
          opportunityId: ticket.opportunity_id,
          summary: ticket.description || ticket.requirement || "",
          productInfo: null,
          testRequirements: [],
          capacityRequirements: null,
          siteConditions: null,
          budget: "",
          timeline: ticket.deadline || "",
          competitors: [],
          pendingQuestions: [],
          attachments: [],
          comments: 0,
        };
      });

      setSurveys(transformedSurveys);
    } catch (err) {
      console.error("Failed to load surveys:", err);
      setError(err.response?.data?.detail || err.message || "加载调研记录失败");
      setSurveys([]);
    } finally {
      setLoading(false);
    }
  }, [
    contextOpportunityId,
    contextOpportunityIdNumber,
    contextProjectId,
    contextProjectIdNumber,
    contextTicketId,
    contextTicketIdNumber,
    selectedStatus,
    searchTerm,
  ]);

  useEffect(() => {
    loadSurveys();
  }, [loadSurveys]);

  // 筛选调研记录
  const filteredSurveys = (surveys || []).filter((survey) => {
    const matchesStatus =
      selectedStatus === "all" || survey.status === selectedStatus;
    const matchesMethod =
      selectedMethod === "all" || survey.method === selectedMethod;
    const searchLower = searchTerm.toLowerCase();
    const matchesSearch =
      (survey.customer || "").toLowerCase().includes(searchLower) ||
      (survey.opportunity || "").toLowerCase().includes(searchLower) ||
      (survey.code || "").toLowerCase().includes(searchLower);
    return matchesStatus && matchesMethod && matchesSearch;
  });

  // 统计数据
  const stats = {
    total: surveys.length,
    scheduled: (surveys || []).filter((s) => s.status === "scheduled").length,
    completed: (surveys || []).filter((s) => s.status === "completed").length,
    pendingQuestions: (surveys || []).reduce(
      (acc, s) => acc + s.pendingQuestions?.length,
      0,
    ),
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {!embedded && (
        <PageHeader
          title="需求调研"
          description="管理客户需求调研记录、现场勘察、问题跟踪"
          actions={
            <motion.div variants={fadeIn} className="flex gap-2">
              <Button className="flex items-center gap-2">
                <Plus className="w-4 h-4" />
                新建调研
              </Button>
            </motion.div>
          }
        />
      )}

      {/* 统计卡片 */}
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-2 sm:grid-cols-4 gap-4"
      >
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-slate-500/10 flex items-center justify-center">
                <ClipboardList className="w-5 h-5 text-slate-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">全部调研</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <Calendar className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">已排期</p>
                <p className="text-2xl font-bold text-blue-400">
                  {stats.scheduled}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                <CheckCircle className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">已完成</p>
                <p className="text-2xl font-bold text-emerald-400">
                  {stats.completed}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">待确认问题</p>
                <p className="text-2xl font-bold text-amber-400">
                  {stats.pendingQuestions}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 工具栏 */}
      <motion.div
        variants={fadeIn}
        className="bg-surface-100/50 backdrop-blur-lg rounded-xl border border-white/5 shadow-lg p-4"
      >
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          {/* 搜索 */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              type="text"
              placeholder="搜索客户、商机、调研编号..."
              value={searchTerm || "unknown"}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 w-full"
            />
          </div>

          {/* 筛选 */}
          <div className="flex items-center gap-3 flex-wrap">
            <select
              value={selectedStatus || "unknown"}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-surface-50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {(surveyStatuses || []).map((status) => (
                <option key={status.id} value={status.id}>
                  {status.name}
                </option>
              ))}
            </select>
            <select
              value={selectedMethod || "unknown"}
              onChange={(e) => setSelectedMethod(e.target.value)}
              className="bg-surface-50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="all">全部方式</option>
              {(surveyMethods || []).map((method) => (
                <option key={method.id} value={method.id}>
                  {method.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </motion.div>

      {/* 加载状态 */}
      {loading && (
        <div className="text-center py-16 text-slate-400">
          <ClipboardList className="w-12 h-12 mx-auto mb-4 text-slate-600 animate-pulse" />
          <p className="text-lg font-medium">加载中...</p>
        </div>
      )}

      {/* 错误提示 */}
      {error && !loading && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* 调研列表 */}
      {!loading && !error && (
        <motion.div
          variants={fadeIn}
          className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"
        >
          {filteredSurveys.length > 0 ? (
            (filteredSurveys || []).map((survey) => (
              <SurveyCard
                key={survey.id}
                survey={survey}
                onClick={setSelectedSurvey}
              />
            ))
          ) : (
            <div className="col-span-full text-center py-16 text-slate-400">
              <ClipboardList className="w-12 h-12 mx-auto mb-4 text-slate-600" />
              <p className="text-lg font-medium">暂无调研记录</p>
              <p className="text-sm">请调整筛选条件或创建新调研</p>
            </div>
          )}
        </motion.div>
      )}

      {/* 调研详情面板 */}
      {selectedSurvey && (
        <SurveyDetailPanel
          survey={selectedSurvey}
          onClose={() => setSelectedSurvey(null)}
        />
      )}
    </motion.div>
  );
}
