/**
 * 库存周转率分析页面
 * 分析库存周转情况，识别滞销物料
 */

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, Calendar } from 'lucide-react';
import TurnoverChart from './components/TurnoverChart';
import InventoryAPI from '@/services/inventory';
import { TurnoverAnalysis as ITurnoverAnalysis } from '@/types/inventory';

const TurnoverAnalysisPage: React.FC = () => {
  const [analysis, setAnalysis] = useState<ITurnoverAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    start_date: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000)
      .toISOString()
      .split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
  });

  useEffect(() => {
    loadAnalysis();
  }, []);

  const loadAnalysis = async () => {
    try {
      setLoading(true);
      const data = await InventoryAPI.getTurnoverAnalysis(filters);
      setAnalysis(data);
    } catch (error) {
      console.error('加载周转率分析失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTurnoverRateLevel = (rate: number) => {
    if (rate > 6)
      return { label: '快速周转', color: 'bg-green-100 text-green-800', icon: '🚀' };
    if (rate >= 3)
      return { label: '正常周转', color: 'bg-blue-100 text-blue-800', icon: '✅' };
    return { label: '缓慢周转', color: 'bg-orange-100 text-orange-800', icon: '⚠️' };
  };

  // 模拟月度数据（实际应从API获取）
  const monthlyData = [
    { month: '10月', turnover_rate: 2.8, turnover_days: 130 },
    { month: '11月', turnover_rate: 3.2, turnover_days: 113 },
    { month: '12月', turnover_rate: 3.5, turnover_days: 104 },
    { month: '1月', turnover_rate: 3.1, turnover_days: 117 },
    { month: '2月', turnover_rate: 3.4, turnover_days: 107 },
  ];

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <TrendingUp className="h-8 w-8 text-blue-500" />
          库存周转率分析
        </h1>
        <p className="text-gray-500 mt-1">分析库存周转效率，识别滞销物料</p>
      </div>

      {/* 筛选条件 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            分析周期
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label>开始日期</Label>
              <Input
                type="date"
                value={filters.start_date}
                onChange={(e) =>
                  setFilters({ ...filters, start_date: e.target.value })
                }
              />
            </div>
            <div>
              <Label>结束日期</Label>
              <Input
                type="date"
                value={filters.end_date}
                onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
              />
            </div>
            <div className="flex items-end">
              <Button onClick={loadAnalysis} disabled={loading} className="w-full">
                {loading ? '分析中...' : '分析'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 关键指标 */}
      {analysis && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-gray-600">出库总额</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                ¥{analysis.total_issue_value.toLocaleString()}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-gray-600">平均库存</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                ¥{analysis.avg_stock_value.toLocaleString()}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-gray-600">周转率</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <div className="text-2xl font-bold text-purple-600">
                  {analysis.turnover_rate.toFixed(2)}
                </div>
                <Badge className={getTurnoverRateLevel(analysis.turnover_rate).color}>
                  {getTurnoverRateLevel(analysis.turnover_rate).icon}{' '}
                  {getTurnoverRateLevel(analysis.turnover_rate).label}
                </Badge>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-gray-600">周转天数</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">
                {analysis.turnover_days} 天
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {analysis.period_days} 天周期
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 周转率趋势图 */}
      <Card>
        <CardHeader>
          <CardTitle>周转率趋势</CardTitle>
        </CardHeader>
        <CardContent>
          <TurnoverChart data={monthlyData} />
        </CardContent>
      </Card>

      {/* 分析建议 */}
      <Card>
        <CardHeader>
          <CardTitle>分析建议</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {analysis && analysis.turnover_rate > 6 && (
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
                <p className="text-sm text-yellow-800">
                  ⚠️ 周转率过高（&gt;6），可能存在库存不足风险，建议增加安全库存。
                </p>
              </div>
            )}
            {analysis && analysis.turnover_rate < 3 && (
              <div className="p-3 bg-orange-50 border border-orange-200 rounded">
                <p className="text-sm text-orange-800">
                  ⚠️ 周转率偏低（&lt;3），存在呆滞库存风险，建议：
                  <br />
                  1. 检查库龄超过180天的物料
                  <br />
                  2. 考虑促销或内部消化
                  <br />
                  3. 优化采购计划，减少过度备货
                </p>
              </div>
            )}
            {analysis && analysis.turnover_rate >= 3 && analysis.turnover_rate <= 6 && (
              <div className="p-3 bg-green-50 border border-green-200 rounded">
                <p className="text-sm text-green-800">
                  ✅ 库存周转状况良好，维持当前库存策略。
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TurnoverAnalysisPage;
