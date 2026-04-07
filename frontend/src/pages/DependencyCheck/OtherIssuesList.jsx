import { severityColors } from "./constants";

export default function OtherIssuesList({ otherIssues }) {
  if (otherIssues.length === 0) return null;

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-slate-700">
          <AlertOctagon className="w-5 h-5" />
          其他依赖问题
          <Badge variant="secondary">{otherIssues.length} 个</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {otherIssues.map((issue, idx) => (
            <div
              key={idx}
              className={`border rounded-lg p-4 ${
                severityColors[issue.severity] || "border-slate-200"
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="font-medium text-slate-900">{issue.task_name}</div>
                <Badge
                  variant="secondary"
                  className={severityColors[issue.severity]?.split(" ")[0]}
                >
                  {issue.severity}
                </Badge>
              </div>
              <div className="text-sm text-slate-700">{issue.detail}</div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
