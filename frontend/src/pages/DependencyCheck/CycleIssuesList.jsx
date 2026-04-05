import React from "react";
import { AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";

export default function CycleIssuesList({ cycleIssues }) {
  if (cycleIssues.length === 0) return null;

  return (
    <Card className="mb-6 border border-red-200">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-red-700">
          <AlertTriangle className="w-5 h-5" />
          循环依赖详情
          <Badge variant="destructive">{cycleIssues.length} 个</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {cycleIssues.map((cycle, idx) => (
            <div key={idx} className="rounded-md bg-red-50 border border-red-200 p-4">
              <div className="font-medium text-red-900 mb-2">循环 {idx + 1}:</div>
              <div className="flex flex-wrap gap-2">
                {(cycle || []).map((taskName, taskIdx) => (
                  <React.Fragment key={taskIdx}>
                    <span className="text-sm text-red-800">{taskName}</span>
                    {taskIdx < cycle.length - 1 && (
                      <span className="text-red-400">→</span>
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 rounded-md bg-amber-50 border border-amber-200 p-3 text-sm">
          <strong className="text-amber-900">
            ⚠️ 循环依赖无法自动修复，需要手动调整依赖关系或拆分任务。
          </strong>
        </div>
      </CardContent>
    </Card>
  );
}
