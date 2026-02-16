/**
 * 库龄分布饼图组件
 */

import React from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface AgingPieChartProps {
  data: Array<{
    name: string;
    value: number;
    percentage: number;
  }>;
}

const COLORS = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#6b7280'];

const AgingPieChart: React.FC<AgingPieChartProps> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height={350}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percentage }) => `${name}: ${percentage.toFixed(1)}%`}
          outerRadius={120}
          fill="#8884d8"
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: number) => `¥${value.toLocaleString()}`}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
};

export default AgingPieChart;
