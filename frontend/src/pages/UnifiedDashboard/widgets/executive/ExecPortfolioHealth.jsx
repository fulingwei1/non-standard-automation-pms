/**
 * 高管视图 - 项目组合健康度（饼图）
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const COLORS = ['#22c55e', '#eab308', '#f97316', '#ef4444'];

export default function ExecPortfolioHealth({ data }) {
  const labels = data?.labels || ['健康', '关注', '风险', '严重'];
  const values = data?.values || [0, 0, 0, 0];

  const chartData = labels.map((name, i) => ({ name, value: values[i] })).filter(d => d.value > 0);
  const total = values.reduce((a, b) => a + b, 0);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">项目组合健康度</CardTitle>
      </CardHeader>
      <CardContent>
        {total === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">暂无数据</p>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={chartData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" label>
                {chartData.map((_, i) => (
                  <Cell key={i} fill={COLORS[labels.indexOf(chartData[i]?.name)] || COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
