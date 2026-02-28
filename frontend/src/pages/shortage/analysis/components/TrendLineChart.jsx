/**
 * 趋势折线图组件
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ALERT_COLORS } from '../../constants';
import { TrendingUp } from 'lucide-react';

const TrendLineChart = ({ data = [] }) => {
  if (data.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">暂无趋势数据</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>每日预警趋势</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="date"
              stroke="#6B7280"
              style={{ fontSize: '12px' }}
            />
            <YAxis
              stroke="#6B7280"
              style={{ fontSize: '12px' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #E5E7EB',
                borderRadius: '8px',
                padding: '12px',
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="urgent"
              stroke={ALERT_COLORS.URGENT}
              strokeWidth={2}
              name="紧急"
              dot={{ fill: ALERT_COLORS.URGENT, r: 3 }}
            />
            <Line
              type="monotone"
              dataKey="critical"
              stroke={ALERT_COLORS.CRITICAL}
              strokeWidth={2}
              name="严重"
              dot={{ fill: ALERT_COLORS.CRITICAL, r: 3 }}
            />
            <Line
              type="monotone"
              dataKey="warning"
              stroke={ALERT_COLORS.WARNING}
              strokeWidth={2}
              name="警告"
              dot={{ fill: ALERT_COLORS.WARNING, r: 3 }}
            />
            <Line
              type="monotone"
              dataKey="info"
              stroke={ALERT_COLORS.INFO}
              strokeWidth={2}
              name="提示"
              dot={{ fill: ALERT_COLORS.INFO, r: 3 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

export default TrendLineChart;
