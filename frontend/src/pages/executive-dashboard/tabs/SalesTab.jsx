import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui";
import { PieChart, FunnelChart, DualAxesChart } from "../../../components/charts";
import { formatCurrency } from "../../../lib/utils";
import { fadeIn } from "../../../lib/animations";

export function SalesTab({ salesFunnelData, trendData }) {
  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="text-lg text-white">销售漏斗</CardTitle>
            </CardHeader>
            <CardContent>
              {salesFunnelData.length > 0 ? (
                <FunnelChart
                  data={salesFunnelData}
                  xField="stage"
                  yField="value"
                  height={350}
                />
              ) : (
                <div className="text-center py-16 text-slate-500">
                  <p>暂无销售漏斗数据</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="text-lg text-white">
                客户行业分布
              </CardTitle>
            </CardHeader>
            <CardContent>
              <PieChart
                data={[
                  { type: "新能源", value: 35 },
                  { type: "消费电子", value: 28 },
                  { type: "汽车电子", value: 20 },
                  { type: "医疗器械", value: 12 },
                  { type: "其他", value: 5 },
                ]}
                donut
                height={350}
                statistic={{
                  title: "客户总数",
                  content: "156",
                }}
              />
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-lg text-white">销售业绩趋势</CardTitle>
          </CardHeader>
          <CardContent>
            {trendData.length > 0 ? (
              <DualAxesChart
                data={trendData}
                xField="month"
                yField={["amount", "count"]}
                height={300}
                leftFormatter={(v) => formatCurrency(v)}
                rightFormatter={(v) => `${v}个`}
                geometryOptions={[
                  {
                    geometry: "column",
                    columnWidthRatio: 0.4,
                    color: "#3b82f6",
                  },
                  {
                    geometry: "line",
                    smooth: true,
                    color: "#22c55e",
                    point: { size: 4 },
                  },
                ]}
              />
            ) : (
              <div className="text-center py-16 text-slate-500">
                <p>销售业绩趋势数据需要从API获取</p>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </>
  );
}
