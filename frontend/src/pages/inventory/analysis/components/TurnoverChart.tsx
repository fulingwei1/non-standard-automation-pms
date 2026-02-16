/**
 * 周转率图表组件
 * 使用 Recharts 展示周转率趋势
 */

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface TurnoverChartProps {
  data: Array<{
    month: string;
    turnover_rate: number;
    turnover_days: number;
  }>;
}

const TurnoverChart: React.FC<TurnoverChartProps> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height={350}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis yAxisId="left" label={{ value: '周转率', angle: -90, position: 'insideLeft' }} />
        <YAxis
          yAxisId="right"
          orientation="right"
          label={{ value: '周转天数', angle: 90, position: 'insideRight' }}
        />
        <Tooltip />
        <Legend />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="turnover_rate"
          stroke="#8884d8"
          strokeWidth={2}
          name="周转率"
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="turnover_days"
          stroke="#82ca9d"
          strokeWidth={2}
          name="周转天数"
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default TurnoverChart;
