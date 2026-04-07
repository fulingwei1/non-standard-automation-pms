/**
 * Technical Assessment Page - 技术评估页面
 * 支持线索和商机的技术评估
 */

import { useParams } from "react-router-dom";
import { useAssessmentData } from "./hooks/useAssessmentData";
import { exportReport } from "./utils/exportReport";

export default function TechnicalAssessment() {
  const { sourceType, sourceId } = useParams();

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
  } = useAssessmentData(sourceType, sourceId);

  if (loading) {
    return <div className="p-6">加载中...</div>;
  }

  const dimensionScores = assessment?.dimension_scores
    ? JSON.parse(assessment.dimension_scores)
    : null;
  const risks = assessment?.risks ? JSON.parse(assessment.risks) : [];
  const similarCases = assessment?.similar_cases
    ? JSON.parse(assessment.similar_cases)
    : [];
  const conditions = assessment?.conditions
    ? JSON.parse(assessment.conditions)
    : [];

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
