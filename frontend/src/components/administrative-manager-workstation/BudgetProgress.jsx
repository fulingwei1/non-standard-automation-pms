import { motion } from "framer-motion";
import { DollarSign } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Progress
} from "../../components/ui";
import {
  MonthlyTrendChart,
  CategoryBreakdownCard
} from "../../components/administrative/StatisticsCharts";
import { fadeIn } from "../../lib/animations";
import { formatCurrency } from "./utils";

const BudgetProgress = ({ stats }) => {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <DollarSign className="h-5 w-5 text-emerald-400" />
            月度行政预算执行
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">月度预算</p>
                <p className="text-3xl font-bold text-white mt-1">
                  {formatCurrency(stats.monthlyAdminBudget)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-400">已使用</p>
                <p className="text-3xl font-bold text-amber-400 mt-1">
                  {formatCurrency(stats.monthlyAdminSpent)}
                </p>
              </div>
            </div>
            <Progress
              value={stats.budgetUtilization}
              className="h-4 bg-slate-700/50" />

            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">
                使用率: {stats.budgetUtilization}%
              </span>
              <span className="text-slate-400">
                剩余:{" "}
                {formatCurrency(
                  stats.monthlyAdminBudget - stats.monthlyAdminSpent
                )}
              </span>
            </div>
            <div className="pt-4 border-t border-slate-700/50">
              <CategoryBreakdownCard
                title="费用分类"
                data={[
                {
                  label: "办公用品",
                  value: stats.officeSuppliesMonthlyCost || 0,
                  color: "#3b82f6"
                },
                {
                  label: "车辆费用",
                  value: stats.monthlyFuelCost || 0,
                  color: "#06b6d4"
                },
                {
                  label: "其他费用",
                  value:
                  stats.monthlyAdminSpent -
                  (stats.officeSuppliesMonthlyCost || 0) -
                  (stats.monthlyFuelCost || 0),
                  color: "#64748b"
                }]
                }
                total={stats.monthlyAdminSpent}
                formatValue={formatCurrency} />

            </div>

            <div className="pt-4 border-t border-slate-700/50">
              <p className="text-sm text-slate-400 mb-3">月度费用趋势</p>
              <MonthlyTrendChart
                data={[
                { month: "2024-10", amount: 420000 },
                { month: "2024-11", amount: 395000 },
                { month: "2024-12", amount: 410000 },
                { month: "2025-01", amount: stats.monthlyAdminSpent }]
                }
                valueKey="amount"
                labelKey="month"
                height={120} />

            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default BudgetProgress;
