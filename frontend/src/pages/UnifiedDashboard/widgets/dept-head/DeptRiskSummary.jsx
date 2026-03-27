/**
 * 部门负责人视图 - 风险汇总（饼图）
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { ShieldAlert } from 'lucide-react';

const LEVEL_CONFIG = [
  { key: 'critical', label: '严重', color: '#ef4444' },
  { key: 'high', label: '高', color: '#f97316' },
  { key: 'medium', label: '中', color: '#eab308' },
  { key: 'low', label: '低', color: '#22c55e' },
];

export default function DeptRiskSummary({ data }) {
  const chartData = LEVEL_CONFIG
    .map((l) => ({ name: l.label, value: data?.[l.key] || 0, color: l.color }))
    .filter((d) => d.value > 0);

  const total = chartData.reduce((a, b) => a + b.value, 0);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-orange-500" />
          部门风险汇总
        </CardTitle>
      </CardHeader>
      <CardContent>
        {total === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">暂无风险</p>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={chartData} cx="50%" cy="50%" innerRadius={40} outerRadius={70} dataKey="value" label>
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
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
