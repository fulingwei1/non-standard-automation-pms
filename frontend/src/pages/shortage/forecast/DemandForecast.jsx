/**
 * 需求预测页面
 * Team 3 - Material Demand Forecast
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { getForecast } from '@/services/api/shortage';
import AlgorithmSelector from './components/AlgorithmSelector';
import ForecastChart from './components/ForecastChart';
import ConfidenceInterval from './components/ConfidenceInterval';
import { Loader2, Calculator } from 'lucide-react';
import { toast } from '@/hooks/use-toast';

const DemandForecast = () => {
  const [loading, setLoading] = useState(false);
  const [params, setParams] = useState({
    material_id: '',
    algorithm: 'EXP_SMOOTHING',
    forecast_horizon_days: 30,
    historical_days: 90,
    project_id: '',
  });
  const [forecast, setForecast] = useState(null);
  const [historicalData, setHistoricalData] = useState([]);

  // 执行预测
  const handleForecast = async () => {
    if (!params.material_id) {
      toast({
        title: '参数错误',
        description: '请输入物料ID',
        variant: 'destructive',
      });
      return;
    }

    try {
      setLoading(true);
      const response = await getForecast(params.material_id, {
        algorithm: params.algorithm,
        forecast_horizon_days: params.forecast_horizon_days,
        historical_days: params.historical_days,
        project_id: params.project_id || null,
      });

      setForecast(response.data);
      
      // 模拟历史数据（实际应该从API获取）
      const mockHistorical = generateMockHistoricalData(
        params.historical_days,
        response.data.historical_avg
      );
      setHistoricalData(mockHistorical);

      toast({
        title: '预测完成',
        description: `预测需求: ${parseFloat(response.data.forecasted_demand).toFixed(2)}`,
      });
    } catch (error) {
      console.error('Forecast failed:', error);
      toast({
        title: '预测失败',
        description: error.message || '请稍后重试',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">需求预测</h1>
        <p className="text-gray-500 mt-1">
          基于历史数据预测物料需求，支持多种算法
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左侧：参数配置 */}
        <div className="space-y-6">
          {/* 基本参数 */}
          <Card>
            <CardHeader>
              <CardTitle>预测参数</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="material_id">物料ID *</Label>
                <Input
                  id="material_id"
                  type="number"
                  placeholder="输入物料ID"
                  value={params.material_id}
                  onChange={(e) =>
                    setParams({ ...params, material_id: e.target.value })
                  }
                />
              </div>

              <div>
                <Label htmlFor="forecast_horizon_days">预测周期（天）</Label>
                <Input
                  id="forecast_horizon_days"
                  type="number"
                  value={params.forecast_horizon_days}
                  onChange={(e) =>
                    setParams({
                      ...params,
                      forecast_horizon_days: parseInt(e.target.value) || 30,
                    })
                  }
                />
                <p className="text-xs text-gray-500 mt-1">
                  建议: 7-90天
                </p>
              </div>

              <div>
                <Label htmlFor="historical_days">历史数据周期（天）</Label>
                <Input
                  id="historical_days"
                  type="number"
                  value={params.historical_days}
                  onChange={(e) =>
                    setParams({
                      ...params,
                      historical_days: parseInt(e.target.value) || 90,
                    })
                  }
                />
                <p className="text-xs text-gray-500 mt-1">
                  建议: 30-180天
                </p>
              </div>

              <div>
                <Label htmlFor="project_id">项目ID (可选)</Label>
                <Input
                  id="project_id"
                  type="number"
                  placeholder="留空则全局预测"
                  value={params.project_id}
                  onChange={(e) =>
                    setParams({ ...params, project_id: e.target.value })
                  }
                />
              </div>

              <Button
                onClick={handleForecast}
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    预测中...
                  </>
                ) : (
                  <>
                    <Calculator className="mr-2 h-4 w-4" />
                    开始预测
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* 算法选择 */}
          <AlgorithmSelector
            value={params.algorithm}
            onChange={(value) => setParams({ ...params, algorithm: value })}
          />
        </div>

        {/* 右侧：预测结果 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 预测曲线图 */}
          <ForecastChart
            historicalData={historicalData}
            forecastData={forecast}
          />

          {/* 置信区间和准确率 */}
          <ConfidenceInterval forecast={forecast} />
        </div>
      </div>

      {/* 使用说明 */}
      <Card>
        <CardHeader>
          <CardTitle>使用说明</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <h4 className="font-semibold text-blue-600 mb-2">📊 移动平均</h4>
              <p className="text-gray-600">
                计算最近N天的平均需求，适用于需求稳定的物料。
                简单直观，但对突变反应慢。
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-green-600 mb-2">📈 指数平滑 (推荐)</h4>
              <p className="text-gray-600">
                对近期数据赋予更高权重，能较好捕捉趋势变化。
                适用于大多数场景，准确率高。
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-purple-600 mb-2">📉 线性回归</h4>
              <p className="text-gray-600">
                拟合需求趋势线，适用于有明显增长或下降趋势的物料。
                适合长期预测。
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// 生成模拟历史数据（实际应从API获取）
const generateMockHistoricalData = (days, avg) => {
  const data = [];
  const today = new Date();
  
  for (let i = days; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    
    // 生成随机波动
    const variance = avg * 0.2;
    const demand = avg + (Math.random() - 0.5) * variance;
    
    data.push({
      date: date.toISOString().split('T')[0],
      demand: Math.max(0, demand),
    });
  }
  
  return data;
};

export default DemandForecast;
