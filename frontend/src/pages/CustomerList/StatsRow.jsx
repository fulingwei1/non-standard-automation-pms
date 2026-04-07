

import { fadeIn } from "../../lib/animations"

export function StatsRow({ stats }) {
  return (
    <motion.div
      variants={fadeIn}
      className="grid grid-cols-2 sm:grid-cols-4 gap-4"
    >
      <Card className="bg-surface-100/50">
        <CardContent className="p-4 flex items-center gap-4">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <Building2 className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-white">{stats.total}</p>
            <p className="text-xs text-slate-400">客户总数</p>
          </div>
        </CardContent>
      </Card>
      <Card className="bg-surface-100/50">
        <CardContent className="p-4 flex items-center gap-4">
          <div className="p-2 bg-emerald-500/20 rounded-lg">
            <TrendingUp className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-white">{stats.active}</p>
            <p className="text-xs text-slate-400">活跃客户</p>
          </div>
        </CardContent>
      </Card>
      <Card className="bg-surface-100/50">
        <CardContent className="p-4 flex items-center gap-4">
          <div className="p-2 bg-amber-500/20 rounded-lg">
            <Star className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-white">{stats.gradeA}</p>
            <p className="text-xs text-slate-400">A级客户</p>
          </div>
        </CardContent>
      </Card>
      <Card className="bg-surface-100/50">
        <CardContent className="p-4 flex items-center gap-4">
          <div className="p-2 bg-red-500/20 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-red-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-white">{stats.warning}</p>
            <p className="text-xs text-slate-400">需关注</p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
