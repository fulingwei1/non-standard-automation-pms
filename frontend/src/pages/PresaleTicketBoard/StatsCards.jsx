


export default function StatsCards({ stats }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between text-sm text-slate-300">
            工单总量
            <Ticket className="h-4 w-4 text-blue-400" />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-semibold text-white">{stats.total}</div>
          <p className="mt-1 text-xs text-slate-400">待受理 {stats.pending} · 处理中 {stats.inProgress}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between text-sm text-slate-300">
            完成率
            <TrendingUp className="h-4 w-4 text-emerald-400" />
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="text-3xl font-semibold text-emerald-300">
            {stats.completionRate.toFixed(1)}%
          </div>
          <Progress value={stats.completionRate} color="success" />
          <p className="text-xs text-slate-400">已完成 {stats.completed} 单</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between text-sm text-slate-300">
            响应时效
            <Clock3 className="h-4 w-4 text-cyan-400" />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-semibold text-cyan-300">
            {stats.avgResponseHours.toFixed(1)}h
          </div>
          <p className="mt-1 text-xs text-slate-400">
            平均处理周期 {stats.avgHandleHours.toFixed(1)}h
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between text-sm text-slate-300">
            风险工单
            <Gauge className="h-4 w-4 text-amber-400" />
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="text-3xl font-semibold text-amber-300">
            {stats.highPriority + stats.overdue}
          </div>
          <p className="text-xs text-slate-400">
            高优先级 {stats.highPriority} · 超期 {stats.overdue}
          </p>
          <p className="text-xs text-slate-400">按期完结率 {stats.onTimeRate.toFixed(1)}%</p>
        </CardContent>
      </Card>
    </div>
  );
}
