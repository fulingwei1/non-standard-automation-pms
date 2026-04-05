/**
 * CostStructureTab — "成本结构" tab content
 */

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Badge,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui";
import { formatCurrency } from "../../lib/utils";
import { CostStructureChart } from "../../components/cost/CostStructureChart";

export function CostStructureTab({ costStructure, structureByCategory }) {
  if (!costStructure || structureByCategory.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>成本结构分析</CardTitle>
          <CardDescription>按成本分类统计和分析</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-slate-400">
            暂无成本结构数据
          </div>
        </CardContent>
      </Card>
    );
  }

  const categoryCount = costStructure.by_category?.length || 0;
  const averagePct = categoryCount > 0 ? (100 / categoryCount).toFixed(1) : 0;

  const chartData = (structureByCategory || []).map((cat) => ({
    category: cat.category,
    amount: cat.amount,
    percentage: parseFloat(cat.percentage),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>成本结构分析</CardTitle>
        <CardDescription>按成本分类统计和分析</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Summary cards */}
          <div className="grid grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-400">
                  总成本
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatCurrency(costStructure.total_cost || 0)}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-400">
                  成本分类数
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{categoryCount}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-400">
                  平均占比
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{averagePct}%</div>
              </CardContent>
            </Card>
          </div>

          {/* Pie / donut chart */}
          <div className="border border-slate-700 rounded-lg p-6 bg-slate-800/30">
            <CostStructureChart data={chartData} size={300} showLegend />
          </div>

          {/* Structure breakdown table */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>成本分类</TableHead>
                <TableHead>金额</TableHead>
                <TableHead>占比</TableHead>
                <TableHead>趋势</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(structureByCategory || []).map((category, index) => (
                <TableRow key={index}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{
                          backgroundColor: `hsl(${
                            (index * 360) / structureByCategory.length
                          }, 70%, 50%)`,
                        }}
                      />
                      {category.category}
                    </div>
                  </TableCell>
                  <TableCell>{formatCurrency(category.amount || 0)}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-slate-700 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${category.percentage}%` }}
                        />
                      </div>
                      <span className="text-sm w-16 text-right">
                        {category.percentage}%
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className="bg-slate-600">-</Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
