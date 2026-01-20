import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui";
import {
  DualAxesChart,
  ProjectHealthChart,
  CostAnalysisChart,
  DeliveryRateChart,
} from "../../../components/charts";
import { formatCurrency } from "../../../lib/utils";
import { fadeIn } from "../../../lib/animations";

export function OverviewTab({ healthData, deliveryData, trendData, costData }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-lg text-white">
              项目健康度分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ProjectHealthChart
              data={
                Object.keys(healthData).length > 0
                  ? healthData
                  : { H1: 12, H2: 8, H3: 3, H4: 5 }
              }
              chartType="donut"
              height={280}
              title=""
              onHealthClick={(health) =>
                console.log("Health clicked:", health)
              }
            />
          </CardContent>
        </Card>
      </motion.div>

      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-lg text-white">
              交付准时率趋势
            </CardTitle>
          </CardHeader>
          <CardContent>
            {deliveryData.length > 0 ? (
              <DeliveryRateChart
                data={deliveryData}
                chartType="trend"
                height={280}
                title=""
              />
            ) : (
              <DeliveryRateChart
                data={[
                  { month: "7月", rate: 82 },
                  { month: "8月", rate: 85 },
                  { month: "9月", rate: 78 },
                  { month: "10月", rate: 88 },
                  { month: "11月", rate: 92 },
                  { month: "12月", rate: 85 },
                ]}
                chartType="trend"
                height={280}
                title=""
              />
            )}
          </CardContent>
        </Card>
      </motion.div>

      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-lg text-white">
              营收与利润趋势
            </CardTitle>
          </CardHeader>
          <CardContent>
            {trendData.length > 0 ? (
              <DualAxesChart
                data={trendData}
                xField="month"
                yField={["revenue", "profit"]}
                height={280}
                leftFormatter={(v) => formatCurrency(v)}
                rightFormatter={(v) => formatCurrency(v)}
                title=""
              />
            ) : (
              <div className="text-center py-16 text-slate-500">
                <p>暂无趋势数据</p>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-lg text-white">成本构成分析</CardTitle>
          </CardHeader>
          <CardContent>
            {costData.length > 0 ? (
              <CostAnalysisChart
                data={costData}
                chartType="structure"
                height={280}
                title=""
                onCategoryClick={(cat) =>
                  console.log("Category clicked:", cat)
                }
              />
            ) : (
              <div className="text-center py-16 text-slate-500">
                <p>暂无成本数据</p>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
