/**
 * 置信区间和准确率指标组件
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Target, TrendingUp, AlertCircle } from 'lucide-react';

const ConfidenceInterval = ({ forecast }) => {
  if (!forecast) return null;

  const accuracy = forecast.accuracy_score || 0;
  const mape = forecast.mape || 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5 text-green-600" />
          预测准确性分析
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 预测结果 */}
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">预测需求量</span>
            <span className="text-2xl font-bold text-blue-600">
              {parseFloat(forecast.forecasted_demand).toFixed(2)}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">置信区间 (95%)</span>
            <span className="font-semibold text-gray-700">
              {parseFloat(forecast.lower_bound).toFixed(2)} ~ {parseFloat(forecast.upper_bound).toFixed(2)}
            </span>
          </div>
        </div>

        {/* 历史准确率 */}
        {accuracy > 0 && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700 flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                历史预测准确率
              </span>
              <span className="text-2xl font-bold text-green-600">
                {accuracy.toFixed(1)}%
              </span>
            </div>
            <Progress value={accuracy} className="h-3" />
            <p className="text-xs text-gray-500 mt-2">
              {accuracy >= 90 && '预测精度极高，可信度强'}
              {accuracy >= 75 && accuracy < 90 && '预测精度良好，可作为参考'}
              {accuracy >= 60 && accuracy < 75 && '预测精度一般，需结合实际情况'}
              {accuracy < 60 && '预测精度较低，建议谨慎使用'}
            </p>
          </div>
        )}

        {/* 误差指标 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
          {/* MAE */}
          {forecast.mae !== null && (
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <AlertCircle className="h-4 w-4 text-gray-500" />
                <p className="text-xs text-gray-600">MAE (平均绝对误差)</p>
              </div>
              <p className="text-xl font-bold text-gray-900">
                {parseFloat(forecast.mae).toFixed(2)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                误差越小越准确
              </p>
            </div>
          )}

          {/* MAPE */}
          {mape > 0 && (
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <AlertCircle className="h-4 w-4 text-gray-500" />
                <p className="text-xs text-gray-600">MAPE (平均绝对百分比误差)</p>
              </div>
              <p className="text-xl font-bold text-gray-900">
                {mape.toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {mape < 10 && '误差极小'}
                {mape >= 10 && mape < 20 && '误差较小'}
                {mape >= 20 && '误差偏大'}
              </p>
            </div>
          )}
        </div>

        {/* 算法信息 */}
        <div className="pt-4 border-t">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">预测算法</span>
            <Badge variant="outline">{forecast.algorithm}</Badge>
          </div>
          <div className="flex items-center justify-between text-sm mt-2">
            <span className="text-gray-600">历史平均需求</span>
            <span className="font-semibold">
              {parseFloat(forecast.historical_avg || 0).toFixed(2)}
            </span>
          </div>
          {forecast.seasonal_factor && (
            <div className="flex items-center justify-between text-sm mt-2">
              <span className="text-gray-600">季节性系数</span>
              <span className="font-semibold">
                {parseFloat(forecast.seasonal_factor).toFixed(2)}
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default ConfidenceInterval;
