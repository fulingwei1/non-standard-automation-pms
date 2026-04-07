

import { formatDate, formatWan, getStatusConfig } from "./utils";

export default function SolutionVersionsTab({
  solutions,
  selectedSolutionId,
  setSelectedSolutionId,
  versionsError,
  versionsLoading,
  versions,
  selectedVersionId,
  setSelectedVersionId,
  selectedVersion,
}) {
  return (
    <div className="space-y-4">
      <Card className="border-white/10 bg-white/5 backdrop-blur">
        <CardContent className="pt-6">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-medium text-slate-100">选择方案查看版本链</p>
              <p className="text-xs text-slate-400">支持查看历史版本和评审记录</p>
            </div>
            <Select
              value={selectedSolutionId || ""}
              onValueChange={(value) => setSelectedSolutionId(value)}
            >
              <SelectTrigger className="w-full md:w-[320px]">
                <SelectValue placeholder="请选择方案" />
              </SelectTrigger>
              <SelectContent>
                {solutions.map((solution) => (
                  <SelectItem key={solution.id} value={String(solution.id)}>
                    {solution.name} ({solution.version})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {versionsError && (
        <Alert className="border-red-500/30 bg-red-500/10 text-red-100">
          <AlertTitle>版本加载失败</AlertTitle>
          <AlertDescription>{versionsError}</AlertDescription>
        </Alert>
      )}

      {versionsLoading ? (
        <div className="rounded-xl border border-white/10 bg-white/5 py-12 text-center text-slate-300">
          <RefreshCw className="mx-auto mb-3 h-6 w-6 animate-spin" />
          正在加载版本记录...
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-1 border-white/10 bg-white/5">
            <CardHeader>
              <CardTitle className="text-base">版本时间线</CardTitle>
              <CardDescription>共 {versions.length} 个版本</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {versions.length > 0 ? (
                versions.map((version) => {
                  const isActive = String(version.id) === String(selectedVersionId);
                  const statusConfig = getStatusConfig(version.status);
                  return (
                    <button
                      key={version.id}
                      type="button"
                      onClick={() => setSelectedVersionId(String(version.id))}
                      className={`w-full rounded-lg border p-3 text-left transition-colors ${
                        isActive
                          ? "border-cyan-400/60 bg-cyan-500/10"
                          : "border-white/10 bg-white/5 hover:border-white/20"
                      }`}
                    >
                      <div className="mb-2 flex items-center justify-between gap-2">
                        <p className="text-sm font-medium text-slate-100">{version.version}</p>
                        <Badge className={statusConfig.className}>{statusConfig.label}</Badge>
                      </div>
                      <p className="text-xs text-slate-400">{formatDate(version.updatedAt || version.createdAt)}</p>
                    </button>
                  );
                })
              ) : (
                <p className="py-8 text-center text-sm text-slate-400">当前方案暂无版本记录</p>
              )}
            </CardContent>
          </Card>

          <Card className="lg:col-span-2 border-white/10 bg-white/5">
            <CardHeader>
              <CardTitle className="text-base">版本详情</CardTitle>
              <CardDescription>查看方案内容、评审意见与估算信息</CardDescription>
            </CardHeader>
            <CardContent>
              {selectedVersion ? (
                <div className="space-y-5">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-lg font-medium text-slate-100">{selectedVersion.name}</p>
                      <p className="text-xs text-slate-400">
                        {selectedVersion.solutionNo} · {selectedVersion.industry}
                      </p>
                    </div>
                    <Badge className={getStatusConfig(selectedVersion.status).className}>
                      {getStatusConfig(selectedVersion.status).label}
                    </Badge>
                  </div>

                  <div className="grid gap-3 md:grid-cols-2">
                    <div className="rounded-lg border border-white/10 bg-slate-900/60 p-3">
                      <p className="text-xs text-slate-400">需求摘要</p>
                      <p className="mt-1 text-sm text-slate-200">{selectedVersion.requirementSummary}</p>
                    </div>
                    <div className="rounded-lg border border-white/10 bg-slate-900/60 p-3">
                      <p className="text-xs text-slate-400">方案概述</p>
                      <p className="mt-1 text-sm text-slate-200">{selectedVersion.solutionOverview}</p>
                    </div>
                    <div className="rounded-lg border border-white/10 bg-slate-900/60 p-3 md:col-span-2">
                      <p className="text-xs text-slate-400">技术规格</p>
                      <pre className="mt-1 whitespace-pre-wrap text-sm text-slate-200">
                        {selectedVersion.technicalSpec}
                      </pre>
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-3">
                    <div className="rounded-lg border border-white/10 bg-white/5 p-3">
                      <p className="text-xs text-slate-400">预估成本</p>
                      <p className="mt-1 text-sm text-slate-100">{formatWan(selectedVersion.estimatedCost)} 万</p>
                    </div>
                    <div className="rounded-lg border border-white/10 bg-white/5 p-3">
                      <p className="text-xs text-slate-400">建议报价</p>
                      <p className="mt-1 text-sm text-cyan-200">{formatWan(selectedVersion.suggestedPrice)} 万</p>
                    </div>
                    <div className="rounded-lg border border-white/10 bg-white/5 p-3">
                      <p className="text-xs text-slate-400">更新时间</p>
                      <p className="mt-1 text-sm text-slate-100">{formatDate(selectedVersion.updatedAt || selectedVersion.createdAt)}</p>
                    </div>
                  </div>

                  {selectedVersion.reviewComment && (
                    <Alert className="border-amber-400/30 bg-amber-500/10">
                      <AlertTitle className="text-amber-100">评审意见</AlertTitle>
                      <AlertDescription className="text-amber-100/90">
                        {selectedVersion.reviewComment}
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              ) : (
                <div className="py-14 text-center text-slate-400">请选择左侧版本查看详情</div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
