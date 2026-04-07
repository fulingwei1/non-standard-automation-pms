/**
 * Acceptance Management — stats summary cards (total / passed / failed / pending)
 */



const StatsCards = ({ stats }) => {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      className="grid grid-cols-4 gap-4 mb-6"
    >
      <Card className="bg-surface-100/50">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">总记录数</p>
              <p className="text-2xl font-bold text-white">{stats.total}</p>
            </div>
            <FileText className="w-8 h-8 text-slate-400" />
          </div>
        </CardContent>
      </Card>

      <Card className="bg-surface-100/50">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">已通过</p>
              <p className="text-2xl font-bold text-emerald-400">{stats.passed}</p>
            </div>
            <CheckCircle2 className="w-8 h-8 text-emerald-400" />
          </div>
        </CardContent>
      </Card>

      <Card className="bg-surface-100/50">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">已失败</p>
              <p className="text-2xl font-bold text-red-400">{stats.failed}</p>
            </div>
            <XCircle className="w-8 h-8 text-red-400" />
          </div>
        </CardContent>
      </Card>

      <Card className="bg-surface-100/50">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">进行中</p>
              <p className="text-2xl font-bold text-amber-400">{stats.pending}</p>
            </div>
            <Clock className="w-8 h-8 text-amber-400" />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default StatsCards;
