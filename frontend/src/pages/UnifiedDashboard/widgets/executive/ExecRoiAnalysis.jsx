/**
 * 高管视图 - 投资回报率分析
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp } from 'lucide-react';

export default function ExecRoiAnalysis({ data }) {
  const items = data?.items || [];

  const chartData = items.map((d, i) => ({
    name: `部门${d.dept_id || i + 1}`,
    roi: d.roi,
    profit: d.profit / 10000,
    count: d.project_count,
  }));

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <TrendingUp className="h-4 w-4" />
          投资回报率分析
        </CardTitle>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">暂无数据</p>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} unit="%" />
              <Tooltip formatter={(v, name) => [name === 'roi' ? `${v}%` : `${v}万`, name === 'roi' ? 'ROI' : '利润']} />
              <Bar dataKey="roi" fill="#3b82f6" name="ROI" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
