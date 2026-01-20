import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui";
import { LineChart, BarChart, CostAnalysisChart } from "../../../components/charts";
import { formatCurrency } from "../../../lib/utils";
import { fadeIn } from "../../../lib/animations";

export function FinanceTab() {
  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="text-lg text-white">
                预算执行分析
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CostAnalysisChart
                data={[
                  { category: "材料成本", budget: 50000000, actual: 47500000 },
                  { category: "人工成本", budget: 30000000, actual: 28500000 },
                  { category: "外协费用", budget: 15000000, actual: 14500000 },
                  { category: "管理费用", budget: 10000000, actual: 10500000 },
                ]}
                chartType="budget"
                height={300}
              />
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="text-lg text-white">回款进度</CardTitle>
            </CardHeader>
            <CardContent>
              <LineChart
                data={[
                  { month: "7月", plan: 15000000, actual: 14200000 },
                  { month: "8月", plan: 18000000, actual: 17500000 },
                  { month: "9月", plan: 20000000, actual: 19800000 },
                  { month: "10月", plan: 22000000, actual: 21000000 },
                  { month: "11月", plan: 25000000, actual: 24500000 },
                  { month: "12月", plan: 28000000, actual: 26000000 },
                ].flatMap((d) => [
                  { month: d.month, type: "计划", value: d.plan },
                  { month: d.month, type: "实际", value: d.actual },
                ])}
                xField="month"
                yField="value"
                seriesField="type"
                height={300}
                formatter={(v) => formatCurrency(v)}
                colors={["#64748b", "#22c55e"]}
              />
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-lg text-white">项目利润分析</CardTitle>
          </CardHeader>
          <CardContent>
            <BarChart
              data={[
                { project: "BMS老化测试", revenue: 850000, cost: 420000, profit: 430000 },
                { project: "EOL功能测试", revenue: 620000, cost: 498000, profit: 122000 },
                { project: "ICT在线测试", revenue: 450000, cost: 234500, profit: 215500 },
                { project: "AOI视觉检测", revenue: 380000, cost: 320000, profit: 60000 },
                { project: "自动组装线", revenue: 1200000, cost: 850000, profit: 350000 },
              ].flatMap((d) => [
                { project: d.project, type: "营收", value: d.revenue },
                { project: d.project, type: "成本", value: d.cost },
                { project: d.project, type: "利润", value: d.profit },
              ])}
              xField="project"
              yField="value"
              seriesField="type"
              isGroup
              height={350}
              formatter={(v) => formatCurrency(v)}
              colors={["#3b82f6", "#ef4444", "#22c55e"]}
            />
          </CardContent>
        </Card>
      </motion.div>
    </>
  );
}
