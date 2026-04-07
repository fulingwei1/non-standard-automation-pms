

import { statusConfig } from "../utils/pageConstants";

export function AssessmentStatusCard({
  assessment,
  assessments,
  showHistory,
  setShowHistory,
  evaluating,
  onExportReport,
  onApplyAssessment,
  onEvaluate,
}) {
  return (
    <Card className="bg-gray-800 border-gray-700">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>评估状态</CardTitle>
          <div className="flex gap-2">
            {assessments.length > 1 && (
              <Button
                onClick={() => setShowHistory(!showHistory)}
                variant="outline"
              >
                {showHistory ? "隐藏历史" : "查看历史"}
              </Button>
            )}
            {assessment && assessment.status === "COMPLETED" && (
              <Button
                onClick={onExportReport}
                variant="outline"
                className="border-blue-500 text-blue-400 hover:bg-blue-500/10"
              >
                <Download className="w-4 h-4 mr-2" />
                导出报告
              </Button>
            )}
            {!assessment && (
              <Button
                onClick={onApplyAssessment}
                className="bg-blue-600 hover:bg-blue-700"
              >
                申请技术评估
              </Button>
            )}
            {assessment && assessment.status === "PENDING" && (
              <Button
                onClick={onEvaluate}
                disabled={evaluating}
                className="bg-green-600 hover:bg-green-700"
              >
                {evaluating ? "评估中..." : "执行评估"}
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {assessment ? (
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <Badge
                className={
                  statusConfig[assessment.status]?.color || "bg-gray-500"
                }
              >
                {statusConfig[assessment.status]?.label || assessment.status}
              </Badge>
              {assessment.evaluator_name && (
                <span className="text-gray-400">
                  评估人: {assessment.evaluator_name}
                </span>
              )}
              {assessment.evaluated_at && (
                <span className="text-gray-400">
                  评估时间:{" "}
                  {new Date(assessment.evaluated_at).toLocaleString()}
                </span>
              )}
            </div>

            {assessment.total_score !== null && (
              <div className="flex items-center gap-4">
                <div className="text-3xl font-bold">
                  {assessment.total_score}
                </div>
                <div className="text-gray-400">总分 / 100</div>
                <Progress value={assessment.total_score} className="flex-1" />
              </div>
            )}
          </div>
        ) : (
          <div className="text-gray-400">尚未申请技术评估</div>
        )}
      </CardContent>
    </Card>
  );
}
