/**
 * Technical Assessment Page - 技术评估页面
 * 支持线索和商机的技术评估
 */

import { useParams, useSearchParams } from "react-router-dom";
import { PageHeader } from "../../components/layout";
import { useAssessmentData } from "./hooks/useAssessmentData";
import { exportReport } from "./utils/exportReport";
import { AssessmentStatusCard } from "./components/AssessmentStatusCard";
import { AssessmentHistory } from "./components/AssessmentHistory";
import { AssessmentResults } from "./components/AssessmentResults";
import { RequirementDataForm } from "./components/RequirementDataForm";
import { parseAssessmentList, parseAssessmentObject } from "./utils/assessmentPayload";

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
