
export default function SummaryCards({
  cycleIssues,
  timingIssues,
  missingIssues,
  otherIssues,
  autoFixTiming,
  autoFixMissing,
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
      {/* 循环依赖 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm text-slate-600">循环依赖</div>
            <GitBranch
              className={`w-4 h-4 ${
                cycleIssues.length > 0 ? "text-red-500" : "text-emerald-500"
              }`}
            />
          </div>
          <div
            className={`text-3xl font-bold ${
              cycleIssues.length > 0 ? "text-red-600" : "text-emerald-600"
            }`}
          >
            {cycleIssues.length}
          </div>
          <div className="text-sm text-slate-500 mt-1">
            {cycleIssues.length > 0
              ? "存在循环依赖，需要人工处理"
              : "无循环依赖"}
          </div>
        </CardContent>
      </Card>

      {/* 时序冲突 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm text-slate-600">时序冲突</div>
            <AlertTriangle
              className={`w-4 h-4 ${
                timingIssues.length > 0 ? "text-amber-500" : "text-emerald-500"
              }`}
            />
          </div>
          <div
            className={`text-3xl font-bold ${
              timingIssues.length > 0 ? "text-amber-600" : "text-emerald-600"
            }`}
          >
            {timingIssues.length}
          </div>
          <div className="text-sm text-slate-500 mt-1">
            {autoFixTiming ? "将自动修复" : "需要手动调整"}
          </div>
        </CardContent>
      </Card>

      {/* 缺失依赖 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm text-slate-600">缺失依赖</div>
            <Link2
              className={`w-4 h-4 ${
                missingIssues.length > 0 ? "text-blue-500" : "text-emerald-500"
              }`}
            />
          </div>
          <div
            className={`text-3xl font-bold ${
              missingIssues.length > 0 ? "text-blue-600" : "text-emerald-600"
            }`}
          >
            {missingIssues.length}
          </div>
          <div className="text-sm text-slate-500 mt-1">
            {autoFixMissing ? "将自动移除" : "需手动删除"}
          </div>
        </CardContent>
      </Card>

      {/* 其他问题 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm text-slate-600">其他问题</div>
            <AlertOctagon
              className={`w-4 h-4 ${
                otherIssues.length > 0 ? "text-amber-500" : "text-emerald-500"
              }`}
            />
          </div>
          <div
            className={`text-3xl font-bold ${
              otherIssues.length > 0 ? "text-amber-600" : "text-emerald-600"
            }`}
          >
            {otherIssues.length}
          </div>
          <div className="text-sm text-slate-500 mt-1">
            {otherIssues.length > 0 ? "需手动处理" : "无其他问题"}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
