/**
 * TrendCharts — 问题总数趋势图 + 待处理/已解决对比图
 */
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { SimpleLineChart } from "../../components/administrative/StatisticsCharts";

/**
 * @param {{
 *   trendData: {
 *     total: { date: string, value: number }[],
 *     open:  { date: string, value: number }[],
 *     resolved: { date: string, value: number }[],
 *   } | null
 * }} props
 */
export function TrendCharts({ trendData }) {
  if (!trendData) { return null; }

  const toChartData = (arr) =>
    (arr || []).map((item) => ({ label: item.date, value: item.value }));

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card className="bg-surface-50 border-white/5">
        <CardHeader>
          <CardTitle>问题总数趋势</CardTitle>
        </CardHeader>
        <CardContent>
          <SimpleLineChart
            data={toChartData(trendData.total)}
            height={200}
            color="text-blue-400"
          />
        </CardContent>
      </Card>

      <Card className="bg-surface-50 border-white/5">
        <CardHeader>
          <CardTitle>待处理 vs 已解决</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="text-xs text-blue-400 mb-1">待处理</div>
              <SimpleLineChart
                data={toChartData(trendData.open)}
                height={100}
                color="text-blue-400"
              />
            </div>
            <div>
              <div className="text-xs text-green-400 mb-1">已解决</div>
              <SimpleLineChart
                data={toChartData(trendData.resolved)}
                height={100}
                color="text-green-400"
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
