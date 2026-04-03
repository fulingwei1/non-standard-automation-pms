/**
 * Recent Analyses Card - 最近齐套分析
 */
import { Eye } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { cn } from "../../lib/utils";
import { getKitRateColor } from "./constants";

export default function RecentAnalyses({ recentAnalyses, onViewDetail }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>最近齐套分析</CardTitle>
      </CardHeader>
      <CardContent>
        {recentAnalyses.length > 0 ?
        <div className="space-y-3">
            {(recentAnalyses || []).map((analysis) =>
          <div
            key={analysis.id}
            className={cn(
              "p-4 rounded-lg border cursor-pointer hover:bg-slate-50 transition-colors",
              analysis.can_start ?
              "border-emerald-200 bg-emerald-50/50" :
              "border-red-200 bg-red-50/50"
            )}
            onClick={() => onViewDetail(analysis.id)}>

                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium">
                        {analysis.project_name || analysis.project_no}
                      </span>
                      {analysis.machine_no &&
                  <Badge variant="outline">
                          {analysis.machine_no}
                  </Badge>
                  }
                    </div>
                    <div className="text-sm text-slate-500 mb-2">
                      分析时间:{" "}
                      {new Date(analysis.analysis_time).toLocaleString()}
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-1">
                        <span className="text-sm text-slate-500">
                          整体:
                        </span>
                        <span
                      className={cn(
                        "font-medium",
                        getKitRateColor(analysis.overall_kit_rate)
                      )}>

                          {analysis.overall_kit_rate}%
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-sm text-slate-500">
                          阻塞:
                        </span>
                        <span
                      className={cn(
                        "font-medium",
                        getKitRateColor(analysis.blocking_kit_rate)
                      )}>

                          {analysis.blocking_kit_rate}%
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    {analysis.can_start ?
                <Badge className="bg-emerald-500">可开工</Badge> :

                <Badge className="bg-red-500">
                        阻塞于 {analysis.first_blocked_stage}
                </Badge>
                }
                    <Eye className="w-4 h-4 text-slate-400" />
                  </div>
                </div>
          </div>
          )}
        </div> :

        <div className="text-center py-8 text-slate-400">
            暂无分析记录
        </div>
        }
      </CardContent>
    </Card>
  );
}
