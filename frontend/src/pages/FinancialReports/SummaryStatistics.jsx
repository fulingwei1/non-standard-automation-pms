

import { staggerContainer } from "../../lib/animations";
import { formatCurrency } from "../../lib/utils";

export default function SummaryStatistics({ totalRevenue, totalCost, totalProfit, avgMargin, currentData }) {
  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4">

      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-400 mb-2">累计营收</p>
              <p className="text-2xl font-bold text-amber-400">
                {formatCurrency(totalRevenue)}
              </p>
              <div className="flex items-center gap-1 mt-1">
                <TrendingUp className="w-3 h-3 text-emerald-400" />
                <span className="text-xs text-emerald-400">+18.5%</span>
              </div>
            </div>
            <div className="p-2 bg-amber-500/20 rounded-lg">
              <DollarSign className="w-5 h-5 text-amber-400" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-400 mb-2">累计成本</p>
              <p className="text-2xl font-bold text-red-400">
                {formatCurrency(totalCost)}
              </p>
              <div className="flex items-center gap-1 mt-1">
                <TrendingDown className="w-3 h-3 text-red-400" />
                <span className="text-xs text-red-400">-2.3%</span>
              </div>
            </div>
            <div className="p-2 bg-red-500/20 rounded-lg">
              <Receipt className="w-5 h-5 text-red-400" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-400 mb-2">累计利润</p>
              <p className="text-2xl font-bold text-emerald-400">
                {formatCurrency(totalProfit)}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                利润率: {avgMargin.toFixed(1)}%
              </p>
            </div>
            <div className="p-2 bg-emerald-500/20 rounded-lg">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-400 mb-2">现金流</p>
              <p className="text-2xl font-bold text-cyan-400">
                {formatCurrency(currentData.cashFlow)}
              </p>
              <div className="flex items-center gap-1 mt-1">
                <TrendingUp className="w-3 h-3 text-emerald-400" />
                <span className="text-xs text-emerald-400">+8.5%</span>
              </div>
            </div>
            <div className="p-2 bg-cyan-500/20 rounded-lg">
              <Wallet className="w-5 h-5 text-cyan-400" />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
