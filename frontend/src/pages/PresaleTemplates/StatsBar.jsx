

export function StatsBar({ stats }) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Card className="bg-surface-1/50">
        <CardContent className="p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">模板总数</p>
              <p className="mt-1 text-2xl font-semibold text-white">
                {stats.total}
              </p>
            </div>
            <Layers className="h-6 w-6 text-blue-300" />
          </div>
        </CardContent>
      </Card>
      <Card className="bg-surface-1/50">
        <CardContent className="p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">分类覆盖</p>
              <p className="mt-1 text-2xl font-semibold text-white">
                {stats.categories}
              </p>
            </div>
            <Sparkles className="h-6 w-6 text-violet-300" />
          </div>
        </CardContent>
      </Card>
      <Card className="bg-surface-1/50">
        <CardContent className="p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">累计应用</p>
              <p className="mt-1 text-2xl font-semibold text-white">
                {stats.totalApplyCount}
              </p>
            </div>
            <CheckCircle2 className="h-6 w-6 text-emerald-300" />
          </div>
        </CardContent>
      </Card>
      <Card className="bg-surface-1/50">
        <CardContent className="p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">平均评分</p>
              <p className="mt-1 text-2xl font-semibold text-white">
                {stats.averageRating.toFixed(1)}
              </p>
            </div>
            <Star className="h-6 w-6 text-amber-300" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
