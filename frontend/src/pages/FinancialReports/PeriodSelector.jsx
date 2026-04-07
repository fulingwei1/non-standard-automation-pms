import { fadeIn } from "../../lib/animations";

export default function PeriodSelector({ selectedPeriod, setSelectedPeriod, dateRange, setDateRange }) {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="flex gap-2">
              <Button
                variant={selectedPeriod === "month" ? "default" : "ghost"}
                size="sm"
                onClick={() => setSelectedPeriod("month")}>
                月度
              </Button>
              <Button
                variant={selectedPeriod === "quarter" ? "default" : "ghost"}
                size="sm"
                onClick={() => setSelectedPeriod("quarter")}>
                季度
              </Button>
              <Button
                variant={selectedPeriod === "year" ? "default" : "ghost"}
                size="sm"
                onClick={() => setSelectedPeriod("year")}>
                年度
              </Button>
            </div>
            <select
              value={dateRange || "unknown"}
              onChange={(e) => setDateRange(e.target.value)}
              className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary">
              <option value="2024-07">2024年7月</option>
              <option value="2024-08">2024年8月</option>
              <option value="2024-09">2024年9月</option>
              <option value="2024-10">2024年10月</option>
              <option value="2024-11">2024年11月</option>
              <option value="2024-12">2024年12月</option>
              <option value="2025-01">2025年1月</option>
            </select>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
