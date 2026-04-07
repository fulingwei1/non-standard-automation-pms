
export default function TimingIssuesList({ timingIssues, autoFixTiming }) {
  if (timingIssues.length === 0) return null;

  return (
    <Card className="mb-6 border border-amber-200">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-amber-700">
          <AlertTriangle className="w-5 h-5" />
          时序冲突详情
          <Badge variant="secondary">{timingIssues.length} 个</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {timingIssues.map((issue, idx) => (
            <div key={idx} className="border border-amber-200 rounded-lg p-4">
              <div className="font-medium text-slate-900 mb-2">{issue.task_name}</div>
              <div className="text-sm text-amber-700 mb-2">{issue.detail}</div>
              <div className="flex items-center gap-2 text-sm text-slate-600">
                {autoFixTiming ? (
                  <Badge variant="secondary" className="text-emerald-700 bg-emerald-50">
                    将自动修复
                  </Badge>
                ) : (
                  <Badge variant="secondary">需手动调整</Badge>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
