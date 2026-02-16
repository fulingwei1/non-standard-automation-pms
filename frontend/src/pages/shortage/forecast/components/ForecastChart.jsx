/**
 * 预测曲线图组件
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, ComposedChart } from 'recharts';
import { TrendingUp } from 'lucide-react';

const ForecastChart = ({ historicalData = [], forecastData = null }) => {
  if (!forecastData) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">请选择物料并配置参数后进行预测</p>
        </CardContent>
      </Card>
    );
  }

  // 合并历史数据和预测数据
  const chartData = [
    ...historicalData.map((item) => ({
      date: item.date,
      actual: item.demand,
      type: 'historical',
    })),
    {
      date: forecastData.forecast_start_date,
      actual: null,
      forecasted: forecastData.forecasted_demand,
      lowerBound: forecastData.lower_bound,
      upperBound: forecastData.upper_bound,
      type: 'forecast',
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-blue-600" />
          需求预测曲线
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={chartData}>
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
            
            {/* 置信区间（灰色区域） */}
            <Area
              type="monotone"
              dataKey="upperBound"
              stroke="none"
              fill="#9CA3AF"
              fillOpacity={0.2}
              name="置信区间上限"
            />
            <Area
              type="monotone"
              dataKey="lowerBound"
              stroke="none"
              fill="#9CA3AF"
              fillOpacity={0.2}
              name="置信区间下限"
            />
            
            {/* 历史实际需求 */}
            <Line
              type="monotone"
              dataKey="actual"
              stroke="#3B82F6"
              strokeWidth={2}
              dot={{ fill: '#3B82F6', r: 4 }}
              name="历史需求"
            />
            
            {/* 预测需求 */}
            <Line
              type="monotone"
              dataKey="forecasted"
              stroke="#EF4444"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={{ fill: '#EF4444', r: 6 }}
              name="预测需求"
            />
          </ComposedChart>
        </ResponsiveContainer>

        {/* 图例说明 */}
        <div className="mt-6 pt-4 border-t">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-blue-500"></div>
              <span className="text-gray-600">历史实际需求</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-red-500"></div>
              <span className="text-gray-600">预测需求（虚线）</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded bg-gray-400 opacity-40"></div>
              <span className="text-gray-600">95% 置信区间</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ForecastChart;
