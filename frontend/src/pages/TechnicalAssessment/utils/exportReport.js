import { statusConfig, decisionConfig } from "./pageConstants";

/**
 * Export assessment report as JSON file
 */
export function exportReport(assessment, { dimensionScores, risks, similarCases, conditions }) {
  if (!assessment) return;

  const report = {
    评估编号: assessment.id,
    来源类型: assessment.source_type === "LEAD" ? "线索" : "商机",
    来源ID: assessment.source_id,
    评估状态: statusConfig[assessment.status]?.label || assessment.status,
    总分: assessment.total_score,
    决策建议: decisionConfig[assessment.decision]?.label || assessment.decision,
    评估时间: assessment.evaluated_at
      ? new Date(assessment.evaluated_at).toLocaleString()
      : "未评估",
    评估人: assessment.evaluator_name || "未知",
  };

  if (dimensionScores) {
    report["维度评分"] = dimensionScores;
  }

  if (risks.length > 0) {
    report["风险分析"] = risks;
  }

  if (similarCases.length > 0) {
    report["相似案例"] = similarCases;
  }

  if (conditions.length > 0) {
    report["立项条件"] = conditions;
  }

  const dataStr = JSON.stringify(report, null, 2);
  const dataBlob = new Blob([dataStr], { type: "application/json" });
  const url = URL.createObjectURL(dataBlob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `技术评估报告_${assessment.id}_${new Date().toISOString().split("T")[0]}.json`;
  link.click();
  URL.revokeObjectURL(url);
}
