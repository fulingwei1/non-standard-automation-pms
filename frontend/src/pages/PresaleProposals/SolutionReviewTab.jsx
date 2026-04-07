



import { calculateCompleteness, getStatusConfig } from "./utils";

export default function SolutionReviewTab({
  reviewQueue,
  reviewComments,
  setReviewComments,
  reviewActionLoadingId,
  handleReviewAction,
  setSelectedSolutionId,
  setActiveTab,
}) {
  return (
    <div className="space-y-4">
      {reviewQueue.length === 0 ? (
        <div className="rounded-xl border border-dashed border-white/20 py-16 text-center text-slate-400">
          当前没有待评审方案
        </div>
      ) : (
        reviewQueue.map((solution) => {
          const completeness = calculateCompleteness(solution);
          const statusConfig = getStatusConfig(solution.status);
          return (
            <Card key={solution.id} className="border-white/10 bg-white/5 backdrop-blur">
              <CardHeader>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <CardTitle className="text-base">{solution.name}</CardTitle>
                    <CardDescription className="mt-1 text-xs">
                      {solution.solutionNo} · 版本 {solution.version}
                    </CardDescription>
                  </div>
                  <Badge className={statusConfig.className}>{statusConfig.label}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-slate-300">{solution.requirementSummary}</p>

                <div>
                  <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
                    <span>材料完整度</span>
                    <span>{completeness}%</span>
                  </div>
                  <Progress value={completeness} className="h-2" />
                </div>

                <Textarea
                  rows={3}
                  placeholder="填写评审意见（可选）"
                  value={reviewComments[solution.id] || ""}
                  onChange={(event) =>
                    setReviewComments((previous) => ({
                      ...previous,
                      [solution.id]: event.target.value,
                    }))
                  }
                />

                <div className="flex flex-wrap items-center gap-2">
                  <Button
                    onClick={() => handleReviewAction(solution.id, "APPROVED")}
                    disabled={reviewActionLoadingId === solution.id}
                  >
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                    通过评审
                  </Button>
                  <Button
                    variant="outline"
                    className="border-red-400/40 text-red-100 hover:bg-red-500/10"
                    onClick={() => handleReviewAction(solution.id, "REJECTED")}
                    disabled={reviewActionLoadingId === solution.id}
                  >
                    <XCircle className="mr-2 h-4 w-4" />
                    驳回修改
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setSelectedSolutionId(String(solution.id));
                      setActiveTab("versions");
                    }}
                  >
                    <GitBranch className="mr-2 h-4 w-4" />
                    查看版本轨迹
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })
      )}
    </div>
  );
}
