/**
 * 根因分析柱状图组件
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { ROOT_CAUSE_TYPES } from '../../constants';
import { AlertCircle } from 'lucide-react';

const RootCauseBarChart = ({ data = [] }) => {
  if (data.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">暂无根因数据</p>
        </CardContent>
      </Card>
    );
  }

  // 转换数据格式
  const chartData = data.map((item) => ({
    ...item,
    label: ROOT_CAUSE_TYPES[item.cause_type]?.label || item.cause_type,
    color: ROOT_CAUSE_TYPES[item.cause_type]?.color || '#6B7280',
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>缺料原因分布</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="label"
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
            <Bar dataKey="count" name="发生次数" radius={[8, 8, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        {/* 详细统计 */}
        <div className="mt-6 space-y-3">
          {chartData.map((item, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color }}
                ></div>
                <span className="font-medium text-gray-900">{item.label}</span>
              </div>
              <div className="flex items-center gap-6 text-sm">
                <div className="text-right">
                  <p className="text-gray-500">次数</p>
                  <p className="font-semibold text-gray-900">{item.count}</p>
                </div>
                <div className="text-right">
                  <p className="text-gray-500">占比</p>
                  <p className="font-semibold text-gray-900">
                    {item.percentage?.toFixed(1)}%
                  </p>
                </div>
                {item.cost_impact && (
                  <div className="text-right">
                    <p className="text-gray-500">成本影响</p>
                    <p className="font-semibold text-orange-600">
                      ¥{parseFloat(item.cost_impact).toLocaleString()}
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default RootCauseBarChart;
