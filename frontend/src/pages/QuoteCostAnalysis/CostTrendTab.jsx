/**
 * CostTrendTab — "成本趋势" tab content
 */

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui";
import { cn, formatCurrency, formatDate } from "../../lib/utils";
import { CostTrendChart } from "../../components/cost/CostTrendChart";

export function CostTrendTab({ versions }) {
  if (!versions || versions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>成本趋势</CardTitle>
          <CardDescription>分析报价多个版本的成本变化趋势</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-slate-400">暂无版本数据</div>
        </CardContent>
      </Card>
    );
  }

  const chartData = (versions || []).map((v) => ({
    version_no: v.version_no,
    created_at: v.created_at,
    total_price: v.total_price || 0,
    total_cost: v.cost_total || 0,
    gross_margin: v.gross_margin || 0,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>成本趋势</CardTitle>
        <CardDescription>分析报价多个版本的成本变化趋势</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Trend chart */}
          <div className="border border-slate-700 rounded-lg p-4 bg-slate-800/30">
            <CostTrendChart
              data={chartData}
              height={300}
              showGrid
              showPoints
            />
          </div>

          {/* Trend data table */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>版本</TableHead>
                <TableHead>日期</TableHead>
                <TableHead>总价</TableHead>
                <TableHead>总成本</TableHead>
                <TableHead>毛利率</TableHead>
                <TableHead>变化</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(versions || []).map((version, index) => {
                const prevVersion = index > 0 ? versions[index - 1] : null;
                const priceChange = prevVersion
                  ? (version.total_price || 0) - (prevVersion.total_price || 0)
                  : 0;
                const marginChange = prevVersion
                  ? (version.gross_margin || 0) -
                    (prevVersion.gross_margin || 0)
                  : 0;

                return (
                  <TableRow key={version.id}>
                    <TableCell>{version.version_no}</TableCell>
                    <TableCell>{formatDate(version.created_at)}</TableCell>
                    <TableCell>
                      {formatCurrency(version.total_price || 0)}
                    </TableCell>
                    <TableCell>
                      {formatCurrency(version.cost_total || 0)}
                    </TableCell>
                    <TableCell>{version.gross_margin?.toFixed(2)}%</TableCell>
                    <TableCell>
                      {index > 0 && (
                        <div className="space-y-1">
                          <div
                            className={cn(
                              "text-sm",
                              priceChange >= 0
                                ? "text-green-400"
                                : "text-red-400"
                            )}
                          >
                            价格: {priceChange >= 0 ? "+" : ""}
                            {formatCurrency(priceChange)}
                          </div>
                          <div
                            className={cn(
                              "text-sm",
                              marginChange >= 0
                                ? "text-green-400"
                                : "text-red-400"
                            )}
                          >
                            毛利率: {marginChange >= 0 ? "+" : ""}
                            {marginChange.toFixed(2)}%
                          </div>
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
