import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui";
import { BarChart, AreaChart, GaugeChart } from "../../../components/charts";
import { fadeIn } from "../../../lib/animations";

export function ProjectsTab({ milestoneData }) {
  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="text-lg text-white">
                项目阶段分布
              </CardTitle>
            </CardHeader>
            <CardContent>
              <BarChart
                data={[
                  { stage: "S1-需求", count: 3 },
                  { stage: "S2-设计", count: 5 },
                  { stage: "S3-采购", count: 4 },
                  { stage: "S4-制造", count: 6 },
                  { stage: "S5-装配", count: 4 },
                  { stage: "S6-FAT", count: 2 },
                  { stage: "S7-发运", count: 1 },
                  { stage: "S8-SAT", count: 2 },
                  { stage: "S9-质保", count: 1 },
                ]}
                xField="stage"
                yField="count"
                height={250}
                colors={["#3b82f6"]}
                showLabel
              />
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="text-lg text-white">
                项目健康指数
              </CardTitle>
            </CardHeader>
            <CardContent>
              <GaugeChart
                value={milestoneData.healthIndex || 0}
                height={250}
                title="整体健康度"
                unit="%"
              />
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="text-lg text-white">
                里程碑完成率
              </CardTitle>
            </CardHeader>
            <CardContent>
              <GaugeChart
                value={milestoneData.completionRate || 0}
                height={250}
                title="本月里程碑"
                unit="%"
                thresholds={[
                  { value: 0.5, color: "#ef4444" },
                  { value: 0.75, color: "#eab308" },
                  { value: 1, color: "#22c55e" },
                ]}
              />
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-lg text-white">项目进度趋势</CardTitle>
          </CardHeader>
          <CardContent>
            <AreaChart
              data={[
                { week: "W1", completed: 12, inProgress: 8, delayed: 2 },
                { week: "W2", completed: 15, inProgress: 10, delayed: 3 },
                { week: "W3", completed: 18, inProgress: 12, delayed: 2 },
                { week: "W4", completed: 22, inProgress: 9, delayed: 1 },
              ].flatMap((d) => [
                { week: d.week, type: "已完成", value: d.completed },
                { week: d.week, type: "进行中", value: d.inProgress },
                { week: d.week, type: "延期", value: d.delayed },
              ])}
              xField="week"
              yField="value"
              seriesField="type"
              isStack
              height={300}
              colors={["#22c55e", "#3b82f6", "#ef4444"]}
            />
          </CardContent>
        </Card>
      </motion.div>
    </>
  );
}
