import { useState, useEffect } from "react";
import { Link, useParams, useNavigate, useLocation } from "react-router-dom";
import { projectWorkspaceApi } from "../services/api";
import { formatDate, formatCurrency } from "../lib/utils";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  HealthBadge,
  Progress,
  Skeleton,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  toast } from
"../components/ui";
import ProjectBonusPanel from "../components/project/ProjectBonusPanel";
import ProjectMeetingPanel from "../components/project/ProjectMeetingPanel";
import ProjectIssuePanel from "../components/project/ProjectIssuePanel";
import SolutionLibrary from "../components/project/SolutionLibrary";
import {
  ArrowLeft,
  AlertTriangle,
  Briefcase,
  ClipboardCheck,
  Users,
  DollarSign,
  FileText,
  TrendingUp,
  Activity } from
"lucide-react";

const normalizeRiskFactors = (value) => {
  if (Array.isArray(value)) {
    return value.filter(Boolean);
  }
  if (typeof value === "string" && value.trim()) {
    try {
      const parsed = JSON.parse(value);
      if (Array.isArray(parsed)) {
        return parsed.filter(Boolean);
      }
    } catch {
      // Plain comma or Chinese-comma separated text is accepted below.
    }
    return value
      .split(/[、,，]/)
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return [];
};

const formatRiskLevel = (riskLevel) => {
  if (!riskLevel) {
    return "风险待判";
  }
  const text = String(riskLevel);
  return text.includes("风险") ? text : `${text}风险`;
};

function appendContextParam(params, key, value) {
  if (value !== undefined && value !== null && value !== "") {
    params.set(key, String(value));
  }
}

function getFirstValue(item, keys) {
  for (const key of keys) {
    const value = item?.[key];
    if (value !== undefined && value !== null && value !== "") {
      return value;
    }
  }
  return null;
}

const PRESALE_TICKET_TASK_TYPE_MAP = {
  SOLUTION: "solution",
  SOLUTION_DESIGN: "solution",
  SOLUTION_REVIEW: "review",
  TECHNICAL_SUPPORT: "support",
  QUOTATION: "costing",
  COST_ESTIMATE: "costing",
  COST_SUPPORT: "costing",
  TENDER: "bidding",
  TENDER_SUPPORT: "bidding",
  MEETING: "exchange",
  TECHNICAL_EXCHANGE: "exchange",
  SURVEY: "survey",
  REQUIREMENT_RESEARCH: "survey",
  FEASIBILITY_ASSESSMENT: "assessment",
  CONSULT: "survey",
  SITE_VISIT: "survey",
};

function getPresaleTicketTaskFilter(ticketType) {
  const normalizedType = String(ticketType || "").toUpperCase();
  return PRESALE_TICKET_TASK_TYPE_MAP[normalizedType] || "solution";
}

function buildPresaleSolutionPath(solution, ticket, opportunity, project) {
  const solutionId = getFirstValue(solution, ["id", "solution_id", "solutionId"]);
  if (!solutionId) {
    return null;
  }

  const params = new URLSearchParams();
  appendContextParam(
    params,
    "ticket_id",
    getFirstValue(solution, ["ticket_id", "ticketId"]) || ticket?.id,
  );
  appendContextParam(
    params,
    "lead_id",
    getFirstValue(solution, ["lead_id", "leadId"]) ||
      getFirstValue(ticket, ["lead_id", "leadId"]) ||
      getFirstValue(opportunity, ["lead_id", "leadId"]) ||
      getFirstValue(project, ["lead_id", "leadId"]),
  );
  appendContextParam(
    params,
    "opportunity_id",
    getFirstValue(solution, ["opportunity_id", "opportunityId"]) || opportunity?.id,
  );
  appendContextParam(
    params,
    "project_id",
    getFirstValue(solution, ["project_id", "projectId"]) || project?.id,
  );

  const query = params.toString();
  return `/solutions/${solutionId}${query ? `?${query}` : ""}`;
}

function buildPresaleTicketPath(ticket, opportunity, project) {
  const ticketId = getFirstValue(ticket, ["id", "ticket_id", "ticketId"]);
  if (!ticketId) {
    return null;
  }

  const params = new URLSearchParams();
  params.set("tab", "reviews");
  params.set("type", getPresaleTicketTaskFilter(ticket?.ticket_type));
  appendContextParam(params, "ticket_id", ticketId);
  appendContextParam(
    params,
    "lead_id",
    getFirstValue(ticket, ["lead_id", "leadId"]) ||
      getFirstValue(opportunity, ["lead_id", "leadId"]) ||
      getFirstValue(project, ["lead_id", "leadId"]),
  );
  appendContextParam(
    params,
    "opportunity_id",
    getFirstValue(ticket, ["opportunity_id", "opportunityId"]) || opportunity?.id,
  );
  appendContextParam(
    params,
    "project_id",
    getFirstValue(ticket, ["project_id", "projectId"]) || project?.id,
  );

  return `/presales/technical-solutions?${params.toString()}`;
}

function buildOpenItemsPath(openItems, opportunity, project) {
  const primaryItem = openItems?.items?.[0];
  const sourceType = getFirstValue(primaryItem, ["source_type", "sourceType"]);
  const sourceId = getFirstValue(primaryItem, ["source_id", "sourceId"]);
  if (sourceType && sourceId) {
    const normalizedType =
      String(sourceType).toLowerCase() === "opportunity" ? "opportunity" : "lead";
    return `/sales/${normalizedType}/${sourceId}/open-items`;
  }

  if (opportunity?.id) {
    return `/sales/opportunity/${opportunity.id}/open-items`;
  }

  const leadId = getFirstValue(project, ["lead_id", "leadId"]);
  if (leadId) {
    return `/sales/lead/${leadId}/open-items`;
  }

  return null;
}

function buildTechnicalAssessmentPath(assessment, ticket, opportunity, project) {
  const assessmentId = getFirstValue(assessment, ["id", "assessment_id", "assessmentId"]);
  const opportunityId =
    getFirstValue(opportunity, ["id", "opportunity_id", "opportunityId"]) ||
    getFirstValue(ticket, ["opportunity_id", "opportunityId"]) ||
    getFirstValue(project, ["opportunity_id", "opportunityId"]);
  const leadId =
    getFirstValue(ticket, ["lead_id", "leadId"]) ||
    getFirstValue(opportunity, ["lead_id", "leadId"]) ||
    getFirstValue(project, ["lead_id", "leadId"]);

  let sourceType = getFirstValue(assessment, ["source_type", "sourceType"]);
  let sourceId = getFirstValue(assessment, ["source_id", "sourceId"]);

  if (!sourceType || !sourceId) {
    if (opportunityId) {
      sourceType = "opportunity";
      sourceId = opportunityId;
    } else if (leadId) {
      sourceType = "lead";
      sourceId = leadId;
    }
  }

  const normalizedSourceType = String(sourceType || "").toLowerCase().includes("opportunity") ?
    "opportunity" :
    String(sourceType || "").toLowerCase().includes("lead") ?
      "lead" :
      null;

  if (!normalizedSourceType || !sourceId) {
    return null;
  }

  const params = new URLSearchParams();
  appendContextParam(params, "assessment_id", assessmentId);
  appendContextParam(
    params,
    "ticket_id",
    getFirstValue(assessment, ["presale_ticket_id", "presaleTicketId", "ticket_id", "ticketId"]) ||
      getFirstValue(ticket, ["id", "ticket_id", "ticketId"]),
  );
  if (normalizedSourceType === "opportunity") {
    appendContextParam(params, "lead_id", leadId);
  }
  appendContextParam(
    params,
    "project_id",
    getFirstValue(assessment, ["project_id", "projectId"]) ||
      getFirstValue(ticket, ["project_id", "projectId"]) ||
      getFirstValue(project, ["id", "project_id", "projectId"]),
  );

  const query = params.toString();
  return `/sales/assessments/${normalizedSourceType}/${sourceId}${query ? `?${query}` : ""}`;
}

function appendMissingContextParam(params, key, value) {
  if (!params.has(key)) {
    appendContextParam(params, key, value);
  }
}

function buildContextualActionPath(href, context) {
  if (!href || /^https?:\/\//i.test(href)) {
    return href;
  }

  const url = new URL(href, "http://localhost");
  appendMissingContextParam(url.searchParams, "ticket_id", context.ticketId);
  appendMissingContextParam(url.searchParams, "lead_id", context.leadId);
  appendMissingContextParam(url.searchParams, "opportunity_id", context.opportunityId);
  appendMissingContextParam(url.searchParams, "project_id", context.projectId);

  const query = url.searchParams.toString();
  return `${url.pathname}${query ? `?${query}` : ""}${url.hash}`;
}

export default function ProjectWorkspace() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [workspaceData, setWorkspaceData] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    fetchWorkspaceData();
  }, [id]);

  const fetchWorkspaceData = async () => {
    try {
      setLoading(true);
      const response = await projectWorkspaceApi.getWorkspace(id);
      setWorkspaceData(response.data);
    } catch (error) {
      console.error("Failed to load workspace data:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <Skeleton className="h-12 w-64 mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) =>
          <Skeleton key={i} className="h-48" />
          )}
        </div>
      </div>);

  }

  if (!workspaceData) {
    return (
      <div className="p-6">
        <PageHeader title="项目工作空间" />
        <Card>
          <CardContent className="p-6 text-center text-gray-500">
            无法加载项目数据
          </CardContent>
        </Card>
      </div>);

  }

  const {
    project,
    team,
    tasks,
    bonus: _bonus,
    meetings: _meetings,
    issues: _issues,
    solutions: _solutions,
    documents,
    handover_context: handoverContext,
    downstream_context: downstreamContext
  } = workspaceData;
  const handoverStatus = handoverContext?.handover_status;
  const missingLabels = {
    contract: "合同",
    opportunity: "商机",
    technical_assessment: "技术评估",
    presale_solution: "售前方案",
    baseline_cost: "成本基准"
  };
  const missingItems = handoverStatus?.missing || [];
  const quoteVersion = handoverContext?.quote?.version || {};
  const primarySolution = handoverContext?.presale_solutions?.[0];
  const primaryTicket = handoverContext?.presale_tickets?.[0];
  const technicalAssessment = handoverContext?.technical_assessment || {};
  const currentAssessment = technicalAssessment.current;
  const assessmentRisks = technicalAssessment.risks || {};
  const primaryAssessmentRisk = assessmentRisks.items?.[0];
  const openItems = handoverContext?.open_items || {};
  const primaryOpenItem = openItems.items?.[0];
  const primarySolutionPath = buildPresaleSolutionPath(
    primarySolution,
    primaryTicket,
    handoverContext?.opportunity,
    project,
  );
  const primaryTicketPath = buildPresaleTicketPath(
    primaryTicket,
    handoverContext?.opportunity,
    project,
  );
  const openItemsPath = buildOpenItemsPath(
    openItems,
    handoverContext?.opportunity,
    project,
  );
  const technicalAssessmentPath = buildTechnicalAssessmentPath(
    currentAssessment,
    primaryTicket,
    handoverContext?.opportunity,
    project,
  );
  const currentParams = new URLSearchParams(location.search);
  const downstreamActionContext = {
    ticketId:
      currentParams.get("ticket_id") ||
      currentParams.get("ticketId") ||
      getFirstValue(primaryTicket, ["id", "ticket_id", "ticketId"]),
    leadId:
      currentParams.get("lead_id") ||
      currentParams.get("leadId") ||
      getFirstValue(primaryTicket, ["lead_id", "leadId"]) ||
      getFirstValue(handoverContext?.opportunity, ["lead_id", "leadId"]) ||
      getFirstValue(project, ["lead_id", "leadId"]),
    opportunityId:
      currentParams.get("opportunity_id") ||
      currentParams.get("opportunityId") ||
      getFirstValue(primaryTicket, ["opportunity_id", "opportunityId"]) ||
      handoverContext?.opportunity?.id,
    projectId:
      currentParams.get("project_id") ||
      currentParams.get("projectId") ||
      project?.id,
  };
  const primaryTicketRiskFactors = normalizeRiskFactors(
    primaryTicket?.pm_involvement_risk_factors,
  );
  const primaryTicketRiskFactorsText = primaryTicketRiskFactors.join("、");
  const primaryTicketRiskLabel = formatRiskLevel(
    primaryTicket?.pm_involvement_risk_level,
  );
  const primaryTicketPmAssignmentLabel = primaryTicket?.pm_assigned ? "PM已分配" : "PM未分配";
  const quoteCost =
    handoverContext?.baseline_cost?.quote_cost_total ?? quoteVersion.cost_total;
  const presaleCost =
    handoverContext?.baseline_cost?.presale_estimated_cost ??
    primarySolution?.estimated_cost;
  const technicalReviews = downstreamContext?.engineering?.technical_reviews || {};
  const ecns = downstreamContext?.engineering?.ecns || {};
  const bomContext = downstreamContext?.supply_chain?.bom || {};
  const kitting = downstreamContext?.supply_chain?.kitting || {};
  const productionPlans = downstreamContext?.production?.plans || {};
  const workOrders = downstreamContext?.production?.work_orders || {};
  const qualityInspections = downstreamContext?.quality?.inspections || {};
  const deliverySchedules = downstreamContext?.delivery?.schedules || {};
  const deliveryTasks = downstreamContext?.delivery?.tasks || {};
  const acceptanceOrders = downstreamContext?.acceptance?.orders || {};
  const latestReview = technicalReviews.items?.[0];
  const latestEcn = ecns.items?.[0];
  const latestBom = bomContext.items?.[0];
  const latestProductionPlan = productionPlans.items?.[0];
  const latestWorkOrder = workOrders.items?.[0];
  const latestInspection = qualityInspections.items?.[0];
  const latestDeliverySchedule = deliverySchedules.items?.[0];
  const latestAcceptance = acceptanceOrders.items?.[0];
  const firstShortage = kitting.shortage_details?.[0];
  const nextActions = downstreamContext?.next_actions || [];
  const actionDomainLabels = {
    engineering: "工程",
    supply_chain: "供应链",
    production: "生产",
    quality: "质检",
    delivery: "交付",
    acceptance: "验收"
  };
  const actionPriorityLabels = {
    HIGH: "高",
    MEDIUM: "中",
    LOW: "低"
  };

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title={
        <div className="flex items-center gap-3">
            <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(-1)}
            className="p-0 h-auto">

              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold">{project.project_name}</h1>
              <p className="text-sm text-gray-500">{project.project_code}</p>
            </div>
        </div>
        } />


      {/* 项目概览卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">项目进度</p>
                <p className="text-2xl font-bold">{project.progress_pct}%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-blue-500" />
            </div>
            <Progress value={project.progress_pct} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">健康度</p>
                <HealthBadge health={project.health} className="mt-1" />
              </div>
              <Activity className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">团队成员</p>
                <p className="text-2xl font-bold">{team.length}</p>
              </div>
              <Users className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">合同金额</p>
                <p className="text-2xl font-bold">
                  {formatCurrency(project.contract_amount)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 标签页 */}
      <Tabs value={activeTab || "unknown"} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">概览</TabsTrigger>
          <TabsTrigger value="bonus">奖金</TabsTrigger>
          <TabsTrigger value="meetings">会议</TabsTrigger>
          <TabsTrigger value="issues">问题</TabsTrigger>
          <TabsTrigger value="solutions">解决方案</TabsTrigger>
          <TabsTrigger value="documents">文档</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {handoverContext &&
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between gap-3">
                <span className="flex items-center gap-2">
                  <ClipboardCheck className="h-5 w-5" />
                  项目交接包
                </span>
                <Badge variant={handoverStatus?.ready ? "default" : "secondary"}>
                  {handoverStatus?.ready ? "已齐套" : "待补齐"}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {missingItems.length > 0 &&
              <div className="flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-200">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>
                  缺少：{missingItems.map((item) => missingLabels[item] || item).join("、")}
                </span>
              </div>
              }

              <div className="grid grid-cols-1 gap-4 lg:grid-cols-6">
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-gray-500">合同</p>
                  <p className="mt-1 font-medium">
                    {handoverContext.contract?.contract_code || "未关联"}
                  </p>
                  <p className="mt-2 text-sm text-gray-500">
                    {formatCurrency(handoverContext.contract?.total_amount)}
                  </p>
                </div>

                <div className="rounded-lg border p-4">
                  <p className="text-sm text-gray-500">商机</p>
                  <p className="mt-1 font-medium">
                    {handoverContext.opportunity?.opp_code || "未关联"}
                  </p>
                  <p className="mt-2 truncate text-sm text-gray-500">
                    {handoverContext.opportunity?.opp_name || "-"}
                  </p>
                </div>

                <div className="rounded-lg border p-4">
                  <p className="text-sm text-gray-500">报价成本</p>
                  <p className="mt-1 font-medium">
                    {handoverContext.quote?.quote_code || "未关联"}
                  </p>
                  <p className="mt-2 text-sm text-gray-500">
                    {quoteCost != null ? formatCurrency(quoteCost) : "未形成"}
                  </p>
                </div>

                <div className="rounded-lg border p-4">
                  <p className="text-sm text-gray-500">技术评估</p>
                  {technicalAssessmentPath ?
                  <Link className="mt-1 block font-medium text-primary hover:underline" to={technicalAssessmentPath}>
                    {currentAssessment?.total_score != null ?
                    `${currentAssessment.total_score} 分` :
                    "打开技术评估"}
                  </Link> :
                  <p className="mt-1 font-medium">
                    {currentAssessment?.total_score != null ?
                    `${currentAssessment.total_score} 分` :
                    "未完成"}
                  </p>
                  }
                  <div className="mt-2 flex flex-wrap gap-2">
                    <Badge variant={currentAssessment?.status === "COMPLETED" ? "default" : "secondary"}>
                      {currentAssessment?.status === "COMPLETED" ? "已完成" : "待评估"}
                    </Badge>
                    <Badge variant="outline">{assessmentRisks.total || 0} 项风险</Badge>
                  </div>
                  {primaryAssessmentRisk &&
                  <p className="mt-2 truncate text-sm text-gray-500">
                    {primaryAssessmentRisk.risk_title || primaryAssessmentRisk.risk_description}
                  </p>
                  }
                </div>

                <div className="rounded-lg border p-4">
                  <p className="text-sm text-gray-500">售前方案</p>
                  {primarySolutionPath ?
                  <Link className="mt-1 block font-medium text-primary hover:underline" to={primarySolutionPath}>
                    {primarySolution?.name || "未关联"}
                  </Link> :
                  <p className="mt-1 font-medium">{primarySolution?.name || "未关联"}</p>
                  }
                  <p className="mt-2 text-sm text-gray-500">
                    {presaleCost != null ? formatCurrency(presaleCost) : "未估算"}
                  </p>
                </div>

                <div className="rounded-lg border p-4">
                  <p className="text-sm text-gray-500">售前工单</p>
                  {primaryTicketPath ?
                  <Link className="mt-1 block font-medium text-primary hover:underline" to={primaryTicketPath}>
                    {primaryTicket?.ticket_no || "未关联"}
                  </Link> :
                  <p className="mt-1 font-medium">{primaryTicket?.ticket_no || "未关联"}</p>
                  }
                  <p className="mt-2 truncate text-sm text-gray-500">
                    {primaryTicket?.actual_hours != null ?
                    `${primaryTicket.actual_hours} 小时` :
                    primaryTicket?.title || "未记录工时"}
                  </p>
                  {primaryTicket?.pm_involvement_required &&
                  <div className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-2 text-sm text-amber-100">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 shrink-0" />
                      <span className="font-medium">PM提前介入</span>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      <Badge variant="outline">需PM介入</Badge>
                      <Badge variant="outline">{primaryTicketRiskLabel}</Badge>
                      <Badge variant="outline">{primaryTicketPmAssignmentLabel}</Badge>
                    </div>
                    {primaryTicketRiskFactorsText &&
                    <p className="mt-2 text-xs text-amber-100/80">
                      {primaryTicketRiskFactorsText}
                    </p>
                    }
                  </div>
                  }
                </div>
              </div>

              {openItems.total > 0 &&
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <p className="text-sm text-amber-100/80">未闭环事项</p>
                    <p className="mt-1 font-medium text-amber-50">
                      {openItems.total} 项未闭环
                      {openItems.blocking_count > 0 ?
                      `，${openItems.blocking_count} 项阻塞报价/交接` :
                      ""}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant={openItems.blocking_count > 0 ? "destructive" : "outline"}>
                      {openItems.blocking_count > 0 ? "有阻塞" : "待跟进"}
                    </Badge>
                    {openItemsPath &&
                    <Button asChild size="sm" variant="outline">
                      <Link to={openItemsPath}>查看未决事项</Link>
                    </Button>
                    }
                  </div>
                </div>
                {primaryOpenItem &&
                <div className="mt-3 rounded-lg border border-amber-500/20 bg-background/40 p-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="outline">{primaryOpenItem.item_code}</Badge>
                    <Badge variant="outline">{primaryOpenItem.item_type}</Badge>
                  </div>
                  <p className="mt-2 text-sm text-amber-50">
                    {primaryOpenItem.description}
                  </p>
                  <p className="mt-2 text-xs text-amber-100/80">
                    责任方：{primaryOpenItem.responsible_party || "-"}
                    {primaryOpenItem.responsible_person_name ?
                    ` / 责任人：${primaryOpenItem.responsible_person_name}` :
                    ""}
                    {primaryOpenItem.due_date ?
                    ` / 截止：${formatDate(primaryOpenItem.due_date)}` :
                    ""}
                  </p>
                </div>
                }
              </div>
              }
            </CardContent>
          </Card>
          }

          {downstreamContext &&
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                后续模块状态
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-4">
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-gray-500">工程评审</p>
                  <p className="mt-1 font-medium">
                    {latestReview?.review_no || "暂无评审"}
                  </p>
                  <p className="mt-2 truncate text-sm text-gray-500">
                    {latestReview?.review_name || `未完成 ${technicalReviews.open_count || 0} 项`}
                  </p>
                </div>

                <div className="rounded-lg border p-4">
                  <p className="text-sm text-gray-500">ECN</p>
                  <p className="mt-1 font-medium">
                    {latestEcn?.ecn_no || "暂无变更"}
                  </p>
                  <p className="mt-2 truncate text-sm text-gray-500">
                    {latestEcn?.ecn_title || `未关闭 ${ecns.open_count || 0} 项`}
                  </p>
                </div>

                <div className="rounded-lg border p-4">
                  <p className="text-sm text-gray-500">BOM</p>
                  <p className="mt-1 font-medium">
                    {latestBom?.bom_no || "暂无BOM"}
                  </p>
                  <p className="mt-2 truncate text-sm text-gray-500">
                    {latestBom?.bom_name || `共 ${bomContext.total || 0} 份`}
                  </p>
                </div>

                <div className="rounded-lg border p-4">
                  <p className="text-sm text-gray-500">齐套率</p>
                  <p className="mt-1 font-medium">
                    {kitting.kitting_rate != null ? `${kitting.kitting_rate}%` : "未计算"}
                  </p>
                  <p className="mt-2 text-sm text-gray-500">
                    缺料 {kitting.shortage_items || 0} 项
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 lg:grid-cols-4">
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-gray-500">生产/装配</p>
                  <p className="mt-1 font-medium">
                    {latestWorkOrder?.work_order_no || latestProductionPlan?.plan_no || "暂无工单"}
                  </p>
                  <p className="mt-2 truncate text-sm text-gray-500">
                    未完成 {workOrders.open_count || 0} 项，进度 {workOrders.avg_progress ?? 0}%
                  </p>
                </div>

                <div className="rounded-lg border p-4">
                  <p className="text-sm text-gray-500">质检</p>
                  <p className="mt-1 font-medium">
                    {latestInspection?.inspection_no || "暂无质检"}
                  </p>
                  <p className="mt-2 truncate text-sm text-gray-500">
                    不合格 {qualityInspections.failed_count || 0} 项，不良 {qualityInspections.defect_qty || 0}
                  </p>
                </div>

                <div className="rounded-lg border p-4">
                  <p className="text-sm text-gray-500">交付排产</p>
                  <p className="mt-1 font-medium">
                    {latestDeliverySchedule?.schedule_no || "暂无排产"}
                  </p>
                  <p className="mt-2 truncate text-sm text-gray-500">
                    冲突 {deliveryTasks.conflict_count || 0} 项，未完成 {deliveryTasks.open_count || 0} 项
                  </p>
                </div>

                <div className="rounded-lg border p-4">
                  <p className="text-sm text-gray-500">验收</p>
                  <p className="mt-1 font-medium">
                    {latestAcceptance?.order_no || "暂无验收"}
                  </p>
                  <p className="mt-2 truncate text-sm text-gray-500">
                    未完成 {acceptanceOrders.open_count || 0} 单，通过率 {latestAcceptance?.pass_rate ?? 0}%
                  </p>
                </div>
              </div>

              {nextActions.length > 0 &&
              <div className="rounded-lg border p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-medium">后续动作</p>
                  <Badge variant="outline">{nextActions.length} 项</Badge>
                </div>
                <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
                  {nextActions.map((action, index) => {
                    const actionPath = buildContextualActionPath(
                      action.href,
                      downstreamActionContext,
                    );
                    const ActionWrapper = actionPath ? Link : "div";
                    const actionWrapperProps = actionPath ? { to: actionPath } : {};
                    return (
                      <ActionWrapper
                        key={`${action.domain}-${action.title}-${index}`}
                        {...actionWrapperProps}
                        className={`rounded-lg border p-3 ${
                          action.href ?
                          "block transition-colors hover:border-primary/40 hover:bg-white/[0.03]" :
                          ""
                        }`}>

                        <div className="flex items-start justify-between gap-3">
                          <p className="font-medium">{action.title}</p>
                          <div className="flex shrink-0 items-center gap-2">
                            <Badge variant={action.priority === "HIGH" ? "default" : "secondary"}>
                              {actionPriorityLabels[action.priority] || action.priority}
                            </Badge>
                            <Badge variant="outline">
                              {actionDomainLabels[action.domain] || action.domain}
                            </Badge>
                          </div>
                        </div>
                        <p className="mt-2 text-sm text-gray-500">{action.description}</p>
                      </ActionWrapper>
                    );
                  })}
                </div>
              </div>
              }

              {firstShortage &&
              <div className="flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-200">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>
                  关键缺料：<strong>{firstShortage.material_code}</strong> {firstShortage.material_name}
                  ，缺口 {firstShortage.shortage_qty}
                </span>
              </div>
              }
            </CardContent>
          </Card>
          }

          {/* 团队概览 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                项目团队
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {(team || []).map((member) =>
                <div
                  key={member.user_id}
                  className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">

                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{member.user_name}</p>
                        <p className="text-sm text-gray-500">
                          {member.role_code}
                        </p>
                      </div>
                      <Badge variant="outline">{member.allocation_pct}%</Badge>
                    </div>
                    {member.start_date && member.end_date &&
                  <p className="text-xs text-gray-400 mt-2">
                        {member.start_date} ~ {member.end_date}
                  </p>
                  }
                </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 任务概览 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="h-5 w-5" />
                最近任务
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {tasks.slice(0, 10).map((task) =>
                <div
                  key={task.id}
                  className="flex items-center justify-between p-3 border rounded-lg">

                    <div className="flex-1">
                      <p className="font-medium">{task.title}</p>
                      <p className="text-sm text-gray-500">
                        {task.assignee_name}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                      variant={
                      task.status === "COMPLETED" ? "default" : "secondary"
                      }>

                        {task.status}
                      </Badge>
                      <Progress value={task.progress} className="w-20" />
                    </div>
                </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="bonus" className="space-y-6">
          <ProjectBonusPanel projectId={id} />
        </TabsContent>

        <TabsContent value="meetings" className="space-y-6">
          <ProjectMeetingPanel projectId={id} />
        </TabsContent>

        <TabsContent value="issues" className="space-y-6">
          <ProjectIssuePanel projectId={id} />
        </TabsContent>

        <TabsContent value="solutions" className="space-y-6">
          <SolutionLibrary
            projectId={id}
            onApplyTemplate={async (template) => {
              const text =
                template?.solution ||
                template?.solution_template ||
                template?.description_template ||
                "";
              if (!text) {
                toast.info("该模板暂无可复制内容");
                return;
              }
              try {
                await navigator.clipboard.writeText(text);
                toast.success("已复制模板内容到剪贴板");
              } catch {
                toast.info("复制失败，请手动复制模板内容");
              }
            }}
          />

        </TabsContent>

        <TabsContent value="documents" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                项目文档
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {(documents || []).map((doc) =>
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors">

                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-gray-400" />
                      <div>
                        <p className="font-medium">{doc.doc_name}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="outline">{doc.doc_type}</Badge>
                          <span className="text-sm text-gray-500">
                            v{doc.version}
                          </span>
                          <span className="text-sm text-gray-500">
                            {formatDate(doc.created_at)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <Badge
                    variant={
                    doc.status === "APPROVED" ? "default" : "secondary"
                    }>

                      {doc.status}
                    </Badge>
                </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>);

}
