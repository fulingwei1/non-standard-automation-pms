import React from "react";
import { Link2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";

export default function MissingIssuesList({ missingIssues, autoFixMissing }) {
  if (missingIssues.length === 0) return null;

  return (
    <Card className="mb-6 border border-blue-200">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-blue-700">
          <Link2 className="w-5 h-5" />
          缺失依赖详情
          <Badge variant="secondary">{missingIssues.length} 个</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {missingIssues.map((issue, idx) => (
            <div key={idx} className="border border-blue-200 rounded-lg p-4">
              <div className="font-medium text-slate-900 mb-2">{issue.task_name}</div>
              <div className="text-sm text-blue-700 mb-2">{issue.detail}</div>
              <div className="flex items-center gap-2 text-sm text-slate-600">
                {autoFixMissing ? (
                  <Badge variant="secondary" className="text-emerald-700 bg-emerald-50">
                    将自动移除
                  </Badge>
                ) : (
                  <Badge variant="secondary">需手动删除</Badge>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
