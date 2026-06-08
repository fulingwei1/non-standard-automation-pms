/**
 * Technical Assessment Page - 技术评估页面
 * 支持线索和商机的技术评估
 */

import { Link, useParams, useSearchParams } from "react-router-dom";
import { PageHeader } from "../../components/layout";
import { useAssessmentData } from "./hooks/useAssessmentData";
import { exportReport } from "./utils/exportReport";
import { AssessmentStatusCard } from "./components/AssessmentStatusCard";
import { AssessmentHistory } from "./components/AssessmentHistory";
import { AssessmentResults } from "./components/AssessmentResults";
import { RequirementDataForm } from "./components/RequirementDataForm";
import { parseAssessmentList, parseAssessmentObject } from "./utils/assessmentPayload";
import {
  getAssessmentSourceListPath,
  isLeadAssessmentSource,
  normalizeAssessmentSourceType,
} from "../../lib/assessmentSource";

function appendContextParam(params, key, value) {
  if (value !== undefined && value !== null && value !== "") {
    params.set(key, String(value));
  }
}

function buildSourceToolPath(sourceType, sourceId, tool, context = {}) {
  const normalizedSourceType = normalizeAssessmentSourceType(sourceType);
  const params = new URLSearchParams();
  appendContextParam(params, "ticket_id", context.presaleTicketId);
  appendContextParam(params, "lead_id", context.leadId);
  appendContextParam(params, "project_id", context.projectId);
  const query = params.toString();
  return `/sales/${normalizedSourceType}/${sourceId}/${tool}${query ? `?${query}` : ""}`;
}

function CollaborationContextCard({ sourceType, sourceId, collaboration, context }) {
  const openItems = collaboration?.openItems || {};
  const requirementFreezes = collaboration?.requirementFreezes || {};
  const aiClarifications = collaboration?.aiClarifications || {};
  const hasCollaboration =
    (openItems.total || 0) > 0 ||
    (requirementFreezes.total || 0) > 0 ||
    (aiClarifications.total || 0) > 0;
  const cardTone = hasCollaboration
    ? "border-amber-500/30 bg-amber-500/10 text-amber-50"
    : "border-slate-700 bg-slate-800/70 text-slate-100";
  const mutedText = hasCollaboration ? "text-amber-100/90" : "text-slate-300";
  const linkClass = hasCollaboration
    ? "rounded-lg border border-amber-500/40 px-3 py-2 hover:bg-amber-500/10"
    : "rounded-lg border border-slate-600 px-3 py-2 hover:bg-slate-700";

  return (
    <div className={`rounded-2xl border p-5 ${cardTone}`}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h3 className="text-lg font-semibold">售前协作上下文</h3>
          <div className={`mt-2 flex flex-wrap gap-2 text-sm ${mutedText}`}>
            <span>{openItems.total || 0} 项未决，{openItems.blocking_count || 0} 项阻塞</span>
            <span>{requirementFreezes.total || 0} 项需求冻结</span>
            <span>{aiClarifications.total || 0} 轮AI澄清</span>
          </div>
          {!hasCollaboration && (
            <p className="mt-2 text-sm text-slate-400">
              暂无协作记录，可从这里进入创建未决事项、需求冻结或AI澄清。
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-2 text-sm">
          <Link
            className={linkClass}
            to={buildSourceToolPath(sourceType, sourceId, "open-items", context)}
          >
            查看未决事项
          </Link>
          <Link
            className={linkClass}
            to={buildSourceToolPath(sourceType, sourceId, "requirement-freezes", context)}
          >
            查看需求冻结
          </Link>
          <Link
            className={linkClass}
            to={buildSourceToolPath(sourceType, sourceId, "ai-clarifications", context)}
          >
            查看AI澄清
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function TechnicalAssessment() {
  const { sourceType, sourceId } = useParams();
  const [searchParams] = useSearchParams();
  const normalizedSourceType = normalizeAssessmentSourceType(sourceType);
  const selectedAssessmentId = searchParams.get("assessment_id") || searchParams.get("assessmentId");
  const presaleTicketId = searchParams.get("ticket_id") || searchParams.get("ticketId");
  const leadId = searchParams.get("lead_id") || searchParams.get("leadId");
  const projectId = searchParams.get("project_id") || searchParams.get("projectId");

  const {
    assessment,
    setAssessment,
    assessments,
    loading,
    evaluating,
    requirementData,
    setRequirementData,
    collaboration,
    enableAI,
    setEnableAI,
    showHistory,
    setShowHistory,
    assessmentTemplates,
    selectedTemplateId,
    setSelectedTemplateId,
    handleApplyAssessment,
    handleEvaluate,
  } = useAssessmentData(
    normalizedSourceType,
    sourceId,
    selectedAssessmentId,
    presaleTicketId,
    projectId,
  );

  if (loading) {
    return <div className="p-6">加载中...</div>;
  }

  const dimensionScores = parseAssessmentObject(assessment?.dimension_scores);
  const risks = parseAssessmentList(assessment?.risks);
  const similarCases = parseAssessmentList(assessment?.similar_cases);
  const conditions = parseAssessmentList(assessment?.conditions);

  const handleExportReport = () => {
    exportReport(assessment, { dimensionScores, risks, similarCases, conditions });
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <PageHeader
        title="技术评估"
        breadcrumbs={[
          { label: "销售管理", path: "/sales" },
          {
            label: isLeadAssessmentSource(normalizedSourceType) ? "线索管理" : "商机管理",
            path: getAssessmentSourceListPath(normalizedSourceType),
          },
          { label: "技术评估", path: "" },
        ]}
      />

      <div className="mt-6 space-y-6">
        <AssessmentStatusCard
          assessment={assessment}
          assessments={assessments}
          showHistory={showHistory}
          setShowHistory={setShowHistory}
          evaluating={evaluating}
          assessmentTemplates={assessmentTemplates}
          selectedTemplateId={selectedTemplateId}
          onTemplateChange={setSelectedTemplateId}
          onExportReport={handleExportReport}
          onApplyAssessment={handleApplyAssessment}
          onEvaluate={handleEvaluate}
        />

        <CollaborationContextCard
          sourceType={normalizedSourceType}
          sourceId={sourceId}
          collaboration={collaboration}
          context={{ presaleTicketId, leadId, projectId }}
        />

        {showHistory && assessments.length > 1 && (
          <AssessmentHistory
            assessments={assessments}
            currentAssessment={assessment}
            onSelect={setAssessment}
          />
        )}

        {assessment && assessment.status === "COMPLETED" && (
          <AssessmentResults
            assessment={assessment}
            assessments={assessments}
            dimensionScores={dimensionScores}
            risks={risks}
            similarCases={similarCases}
            conditions={conditions}
          />
        )}

        {assessment && assessment.status === "PENDING" && (
          <RequirementDataForm
            requirementData={requirementData}
            setRequirementData={setRequirementData}
            enableAI={enableAI}
            setEnableAI={setEnableAI}
          />
        )}
      </div>
    </div>
  );
}
