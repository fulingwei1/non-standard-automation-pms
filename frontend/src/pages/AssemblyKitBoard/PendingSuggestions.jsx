/**
 * Pending Suggestions Card - 排产建议
 */
import {
  Calendar,
  ThumbsUp,
  ThumbsDown,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { getKitRateColor } from "./constants";

export default function PendingSuggestions({
  pendingSuggestions,
  onAccept,
  onReject,
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="w-5 h-5" />
          排产建议
        </CardTitle>
      </CardHeader>
      <CardContent>
        {pendingSuggestions.length > 0 ?
        <div className="space-y-3">
            {(pendingSuggestions || []).map((suggestion) =>
          <div
            key={suggestion.id}
            className="p-4 rounded-lg border bg-blue-50/50 border-blue-200">

                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="font-medium">
                      {suggestion.project_name || suggestion.project_no}
                    </div>
                    {suggestion.machine_no &&
                <span className="text-sm text-slate-500">
                        {suggestion.machine_no}
                </span>
                }
                  </div>
                  <Badge variant="outline" className="bg-blue-100">
                    {suggestion.suggestion_type === "CAN_START" ?
                "可立即开工" :
                suggestion.suggestion_type === "WAIT_MATERIAL" ?
                "等待物料" :
                suggestion.suggestion_type === "PARTIAL_START" ?
                "部分开工" :
                suggestion.suggestion_type}
                  </Badge>
                </div>
                <div className="text-sm text-slate-600 mb-2">
                  建议开工: {suggestion.suggested_start_date}
                </div>
                <div className="flex items-center gap-2 text-sm mb-3">
                  <span>
                    优先级得分: <strong>{suggestion.priority_score}</strong>
                  </span>
                  <span>
                    齐套率:{" "}
                    <strong
                      className={getKitRateColor(
                        suggestion.current_kit_rate
                      )}>

                      {suggestion.current_kit_rate}%
                    </strong>
                  </span>
                </div>
                {suggestion.score_factors &&
            <div className="text-xs text-slate-500 mb-2 p-2 bg-white rounded">
                    <div className="font-medium mb-1">评分详情：</div>
                    <div className="space-y-1">
                      {Object.entries(suggestion.score_factors).map(
                  ([key, factor]) =>
                  <div key={key} className="flex justify-between">
                            <span>{factor.description || key}:</span>
                            <span className="font-medium">
                              {factor.score}/{factor.max}分
                            </span>
                  </div>

                )}
                    </div>
            </div>
            }
                {suggestion.resource_allocation &&
            <div className="text-xs text-slate-500 mb-2 p-2 bg-white rounded">
                    <div className="font-medium mb-1">资源情况：</div>
                    <div className="space-y-1">
                      <div>
                        可用工位:{" "}
                        {suggestion.resource_allocation.
                  available_workstations || 0}
                        个
                      </div>
                      <div>
                        可用人员:{" "}
                        {suggestion.resource_allocation.available_workers ||
                  0}
                        人
                      </div>
                      {suggestion.resource_allocation.conflicts &&
                suggestion.resource_allocation.conflicts?.length >
                0 &&
                <div className="text-red-500">
                            资源冲突:{" "}
                            {
                  suggestion.resource_allocation.conflicts.
                  length
                  }
                            个
                </div>
                }
                    </div>
            </div>
            }
                {suggestion.reason &&
            <div className="text-sm text-slate-500 mb-3 p-2 bg-white rounded">
                    {suggestion.reason}
            </div>
            }
                <div className="flex gap-2">
                  <Button
                size="sm"
                className="bg-emerald-500 hover:bg-emerald-600"
                onClick={() => onAccept(suggestion.id)}>

                    <ThumbsUp className="w-4 h-4 mr-1" />
                    接受
                  </Button>
                  <Button
                size="sm"
                variant="outline"
                className="border-red-300 text-red-600 hover:bg-red-50"
                onClick={() => onReject(suggestion)}>

                    <ThumbsDown className="w-4 h-4 mr-1" />
                    拒绝
                  </Button>
                </div>
          </div>
          )}
        </div> :

        <div className="text-center py-8 text-slate-400">
            暂无待处理建议
        </div>
        }
      </CardContent>
    </Card>
  );
}
