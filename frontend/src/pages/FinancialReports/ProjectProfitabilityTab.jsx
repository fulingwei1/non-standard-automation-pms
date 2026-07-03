import { TabsContent, Progress } from "../../components/ui";
import { cn, formatCurrency } from "../../lib/utils";
import { BarChart as BarChartComponent } from "../../components/charts";
import { toFiniteNumber } from "./numberUtils";

export default function ProjectProfitabilityTab({ projectProfitability }) {
  return (
    <TabsContent value="project" className="space-y-6 mt-6">
      {/* 项目利润率对比图 */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">
          项目利润率对比
        </h3>
        <BarChartComponent
          data={(projectProfitability || []).map((p) => ({
            project:
            p.project?.length > 8 ?
            p.project.slice(0, 8) + "..." :
            p.project,
            margin: toFiniteNumber(p.margin)
          }))}
          xField="project"
          yField="margin"
          height={250}
          colors={(projectProfitability || []).map((p) =>
          toFiniteNumber(p.margin) >= 30 ?
          "#10b981" :
          toFiniteNumber(p.margin) >= 20 ?
          "#f59e0b" :
          "#ef4444"
          )}
          formatter={(v) => `${v}%`}
          label={{
            position: "top",
            style: { fill: "#94a3b8" },
            formatter: (datum) => `${datum.margin}%`
          }} />
      </div>

      {/* 项目收入成本对比 */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">
          项目收入与成本
        </h3>
        <BarChartComponent
          data={(projectProfitability || []).flatMap((p) => [
          {
            project:
            p.project?.length > 8 ?
            p.project.slice(0, 8) + "..." :
            p.project,
            type: "收入",
            value: toFiniteNumber(p.revenue)
          },
          {
            project:
            p.project?.length > 8 ?
            p.project.slice(0, 8) + "..." :
            p.project,
            type: "成本",
            value: toFiniteNumber(p.cost)
          }]
          )}
          xField="project"
          yField="value"
          seriesField="type"
          isGroup
          height={280}
          colors={["#f59e0b", "#ef4444"]}
          formatter={(v) => `¥${(v / 10000).toFixed(0)}万`} />
      </div>

      {/* 项目盈利明细列表 */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">
          项目盈利明细
        </h3>
        <div className="space-y-3">
          {(projectProfitability || []).map((project, index) => {
            const statusColors = {
              good: "bg-emerald-500",
              warning: "bg-amber-500",
              critical: "bg-red-500"
            };
            const margin = toFiniteNumber(project.margin);
            return (
              <div
                key={index}
                className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-white">
                        {project.project}
                      </span>
                      <div
                        className={cn(
                          "w-2 h-2 rounded-full",
                          statusColors[project.status]
                        )} />
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-amber-400">
                      {formatCurrency(project.revenue)}
                    </div>
                    <div className="text-sm text-emerald-400">
                      利润: {formatCurrency(project.profit)}
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">成本</span>
                    <span className="text-red-400">
                      {formatCurrency(project.cost)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">利润率</span>
                    <span
                      className={cn(
                        "font-medium",
                        margin >= 30 ?
                        "text-emerald-400" :
                        margin >= 20 ?
                        "text-amber-400" :
                        "text-red-400"
                      )}>
                      {margin.toFixed(1)}%
                    </span>
                  </div>
                  <Progress
                    value={margin}
                    className={cn(
                      "h-2",
                      margin >= 30 ?
                      "bg-emerald-500/20" :
                      margin >= 20 ?
                      "bg-amber-500/20" :
                      "bg-red-500/20"
                    )} />
                </div>
              </div>);
          })}
        </div>
      </div>
    </TabsContent>
  );
}
