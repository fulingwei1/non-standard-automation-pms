import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui";
import { AreaChart, UtilizationChart } from "../../../components/charts";
import { fadeIn } from "../../../lib/animations";

export function ResourcesTab({ utilizationData }) {
  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="text-lg text-white">
                人员利用率排名
              </CardTitle>
            </CardHeader>
            <CardContent>
              {utilizationData.length > 0 ? (
                <UtilizationChart
                  data={utilizationData}
                  chartType="bar"
                  height={350}
                  onPersonClick={(person) =>
                    console.log("Person clicked:", person)
                  }
                />
              ) : (
                <div className="text-center py-16 text-slate-500">
                  <p>暂无利用率数据</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="text-lg text-white">部门负荷对比</CardTitle>
            </CardHeader>
            <CardContent>
              <UtilizationChart
                data={[
                  { department: "机械部", rate: 85 },
                  { department: "电气部", rate: 78 },
                  { department: "软件部", rate: 72 },
                  { department: "项目部", rate: 90 },
                  { department: "采购部", rate: 65 },
                  { department: "质量部", rate: 70 },
                ]}
                chartType="radar"
                height={350}
              />
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-lg text-white">资源分配趋势</CardTitle>
          </CardHeader>
          <CardContent>
            <AreaChart
              data={[
                { week: "W1", 机械部: 320, 电气部: 280, 软件部: 240 },
                { week: "W2", 机械部: 350, 电气部: 300, 软件部: 260 },
                { week: "W3", 机械部: 380, 电气部: 320, 软件部: 280 },
                { week: "W4", 机械部: 360, 电气部: 340, 软件部: 300 },
              ].flatMap((d) => [
                { week: d.week, department: "机械部", hours: d.机械部 },
                { week: d.week, department: "电气部", hours: d.电气部 },
                { week: d.week, department: "软件部", hours: d.软件部 },
              ])}
              xField="week"
              yField="hours"
              seriesField="department"
              isStack
              height={300}
              formatter={(v) => `${v}h`}
            />
          </CardContent>
        </Card>
      </motion.div>
    </>
  );
}
