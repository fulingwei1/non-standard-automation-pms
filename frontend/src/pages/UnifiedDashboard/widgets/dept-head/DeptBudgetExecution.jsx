/**
 * 部门负责人视图 - 预算执行率统计
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Wallet } from 'lucide-react';

export default function DeptBudgetExecution({ data }) {
  const items = data?.items || [];

  const chartData = items.map((d) => ({
    name: d.project_name,
    budget: d.budget / 10000,
    actual: d.actual / 10000,
    rate: d.rate,
  }));

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Wallet className="h-4 w-4" />
          预算执行率统计
        </CardTitle>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">暂无数据</p>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" unit="万" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={80} />
              <Tooltip formatter={(v) => `${v.toFixed(1)}万`} />
              <Legend />
              <Bar dataKey="budget" fill="#93c5fd" name="预算" />
              <Bar dataKey="actual" fill="#3b82f6" name="实际" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
