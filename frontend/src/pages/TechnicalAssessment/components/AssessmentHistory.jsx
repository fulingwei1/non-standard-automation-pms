import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
} from "../../../components/ui";
import { statusConfig, decisionConfig } from "../utils/pageConstants";

export function AssessmentHistory({ assessments, currentAssessment, onSelect }) {
  return (
    <Card className="bg-gray-800 border-gray-700">
      <CardHeader>
        <CardTitle>评估历史记录</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {(assessments || []).map((item) => {
            const itemScores = item.dimension_scores
              ? JSON.parse(item.dimension_scores)
              : null;
            return (
              <div
                key={item.id}
                className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                  item.id === currentAssessment?.id
                    ? "bg-blue-900/30 border-blue-500"
                    : "bg-gray-700 border-gray-600 hover:border-gray-500"
                }`}
                onClick={() => onSelect(item)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Badge
                      className={
                        statusConfig[item.status]?.color || "bg-gray-500"
                      }
                    >
                      {statusConfig[item.status]?.label || item.status}
                    </Badge>
                    {item.total_score !== null && (
                      <span className="text-lg font-bold">
                        {item.total_score}分
                      </span>
                    )}
                    {item.decision && (
                      <Badge
                        className={
                          decisionConfig[item.decision]?.color || "bg-gray-500"
                        }
                      >
                        {decisionConfig[item.decision]?.label || item.decision}
                      </Badge>
                    )}
                  </div>
                  <span className="text-xs text-gray-400">
                    {item.evaluated_at
                      ? new Date(item.evaluated_at).toLocaleString()
                      : "未评估"}
                  </span>
                </div>
                {itemScores && (
                  <div className="grid grid-cols-5 gap-2 mt-2">
                    {Object.entries(itemScores).map(([dim, score]) => (
                      <div key={dim} className="text-center">
                        <div className="text-xs text-gray-400">{dim}</div>
                        <div className="text-sm font-semibold">{score}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
