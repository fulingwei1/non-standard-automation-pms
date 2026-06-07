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

function buildSourceToolPath(sourceType, sourceId, tool) {
  return `/sales/${sourceType}/${sourceId}/${tool}`;
}

function CollaborationContextCard({ sourceType, sourceId, collaboration }) {
  const openItems = collaboration?.openItems || {};
  const requirementFreezes = collaboration?.requirementFreezes || {};
  const aiClarifications = collaboration?.aiClarifications || {};
  const hasCollaboration =
    (openItems.total || 0) > 0 ||
    (requirementFreezes.total || 0) > 0 ||
    (aiClarifications.total || 0) > 0;

  if (!hasCollaboration) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-5 text-amber-50">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h3 className="text-lg font-semibold">售前协作上下文</h3>
          <div className="mt-2 flex flex-wrap gap-2 text-sm text-amber-100/90">
            <span>{openItems.total || 0} 项未决，{openItems.blocking_count || 0} 项阻塞</span>
            <span>{requirementFreezes.total || 0} 项需求冻结</span>
            <span>{aiClarifications.total || 0} 轮AI澄清</span>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 text-sm">
          <Link
            className="rounded-lg border border-amber-500/40 px-3 py-2 hover:bg-amber-500/10"
            to={buildSourceToolPath(sourceType, sourceId, "open-items")}
          >
            查看未决事项
          </Link>
          <Link
            className="rounded-lg border border-amber-500/40 px-3 py-2 hover:bg-amber-500/10"
            to={buildSourceToolPath(sourceType, sourceId, "requirement-freezes")}
          >
            查看需求冻结
          </Link>
          <Link
            className="rounded-lg border border-amber-500/40 px-3 py-2 hover:bg-amber-500/10"
            to={buildSourceToolPath(sourceType, sourceId, "ai-clarifications")}
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
  const selectedAssessmentId = searchParams.get("assessment_id") || searchParams.get("assessmentId");
  const presaleTicketId = searchParams.get("ticket_id") || searchParams.get("ticketId");

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
    handleApplyAssessment,
    handleEvaluate,
  } = useAssessmentData(sourceType, sourceId, selectedAssessmentId, presaleTicketId);

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
            label: sourceType === "lead" ? "线索管理" : "商机管理",
            path: sourceType === "lead" ? "/leads" : "/opportunities",
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
          onExportReport={handleExportReport}
          onApplyAssessment={handleApplyAssessment}
          onEvaluate={handleEvaluate}
        />

        <CollaborationContextCard
          sourceType={sourceType}
          sourceId={sourceId}
          collaboration={collaboration}
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
