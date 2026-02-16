/**
 * 库龄分析页面
 * 分析库存物料的库龄分布，识别呆滞库存
 */

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Clock, AlertTriangle } from 'lucide-react';
import AgingPieChart from './components/AgingPieChart';
import InventoryAPI from '@/services/inventory';
import { AgingAnalysisResponse } from '@/types/inventory';

const AgingAnalysisPage: React.FC = () => {
  const [analysis, setAnalysis] = useState<AgingAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [location, setLocation] = useState('');

  useEffect(() => {
    loadAnalysis();
  }, []);

  const loadAnalysis = async () => {
    try {
      setLoading(true);
      const data = await InventoryAPI.getAgingAnalysis(
        location ? { location } : undefined
      );
      setAnalysis(data);
    } catch (error) {
      console.error('加载库龄分析失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getAgingRangeColor = (range: string) => {
    const colors: Record<string, string> = {
      '0-30天': 'bg-green-100 text-green-800',
      '31-90天': 'bg-blue-100 text-blue-800',
      '91-180天': 'bg-orange-100 text-orange-800',
      '181-365天': 'bg-red-100 text-red-800',
      '365天以上': 'bg-gray-100 text-gray-800',
    };
    return colors[range] || 'bg-gray-100 text-gray-800';
  };

  const getPieChartData = () => {
    if (!analysis) return [];
    return Object.entries(analysis.aging_summary).map(([key, value]) => ({
      name: key,
      value: value.total_value,
      percentage: value.percentage,
    }));
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Clock className="h-8 w-8 text-orange-500" />
          库龄分析
        </h1>
        <p className="text-gray-500 mt-1">分析库存物料的库龄分布，识别呆滞库存</p>
      </div>

      {/* 筛选条件 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">筛选条件</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>仓库位置</Label>
              <Input
                placeholder="输入仓库位置（可选）"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
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

      {analysis && (
        <>
          {/* 库龄分布汇总 */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {Object.entries(analysis.aging_summary).map(([range, data]) => (
              <Card key={range}>
                <CardHeader className="pb-2">
                  <Badge className={getAgingRangeColor(range)}>{range}</Badge>
                </CardHeader>
                <CardContent>
                  <div className="space-y-1">
                    <div className="text-xl font-bold">
                      ¥{data.total_value.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600">
                      {data.count} 项 · {data.total_quantity.toLocaleString()} 件
                    </div>
                    <div className="text-xs text-gray-500">
                      占比: {data.percentage.toFixed(1)}%
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* 库龄分布饼图 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>库龄分布（按金额）</CardTitle>
              </CardHeader>
              <CardContent>
                <AgingPieChart data={getPieChartData()} />
              </CardContent>
            </Card>

            {/* 呆滞库存预警 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-500" />
                  呆滞库存预警
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {analysis.aging_summary['181-365天'].count > 0 && (
                    <div className="p-3 bg-orange-50 border border-orange-200 rounded">
                      <p className="font-medium text-orange-800">
                        ⚠️ 181-365天库龄物料
                      </p>
                      <p className="text-sm text-orange-700 mt-1">
                        {analysis.aging_summary['181-365天'].count} 项，金额 ¥
                        {analysis.aging_summary['181-365天'].total_value.toLocaleString()}
                      </p>
                      <p className="text-xs text-orange-600 mt-1">
                        建议：考虑促销或内部消化
                      </p>
                    </div>
                  )}
                  {analysis.aging_summary['365天以上'].count > 0 && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded">
                      <p className="font-medium text-red-800">🚨 365天以上库龄物料</p>
                      <p className="text-sm text-red-700 mt-1">
                        {analysis.aging_summary['365天以上'].count} 项，金额 ¥
                        {analysis.aging_summary['365天以上'].total_value.toLocaleString()}
                      </p>
                      <p className="text-xs text-red-600 mt-1">
                        建议：立即处理，降价或报废
                      </p>
                    </div>
                  )}
                  {analysis.aging_summary['91-180天'].count > 0 && (
                    <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
                      <p className="font-medium text-yellow-800">
                        ℹ️ 91-180天库龄物料
                      </p>
                      <p className="text-sm text-yellow-700 mt-1">
                        {analysis.aging_summary['91-180天'].count} 项，金额 ¥
                        {analysis.aging_summary['91-180天'].total_value.toLocaleString()}
                      </p>
                      <p className="text-xs text-yellow-600 mt-1">
                        建议：关注需求变化，考虑调整库存策略
                      </p>
                    </div>
                  )}
                  {analysis.aging_summary['181-365天'].count === 0 &&
                    analysis.aging_summary['365天以上'].count === 0 &&
                    analysis.aging_summary['91-180天'].count === 0 && (
                      <div className="p-3 bg-green-50 border border-green-200 rounded">
                        <p className="font-medium text-green-800">
                          ✅ 库存健康，无明显呆滞库存
                        </p>
                        <p className="text-sm text-green-700 mt-1">
                          大部分库存在正常周转周期内
                        </p>
                      </div>
                    )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 呆滞物料明细 */}
          {analysis.details.filter((d) => d.in_stock_days > 180).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>呆滞物料明细（库龄&gt;180天）</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>物料编码</TableHead>
                      <TableHead>物料名称</TableHead>
                      <TableHead>批次号</TableHead>
                      <TableHead className="text-right">数量</TableHead>
                      <TableHead className="text-right">金额</TableHead>
                      <TableHead className="text-right">库龄（天）</TableHead>
                      <TableHead>库龄范围</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {analysis.details
                      .filter((d) => d.in_stock_days > 180)
                      .map((detail, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-medium">
                            {detail.material_code}
                          </TableCell>
                          <TableCell>{detail.material_name}</TableCell>
                          <TableCell className="text-sm">
                            {detail.batch_number || '-'}
                          </TableCell>
                          <TableCell className="text-right">
                            {detail.quantity.toLocaleString()}
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            ¥{detail.total_value.toLocaleString()}
                          </TableCell>
                          <TableCell className="text-right text-red-600 font-medium">
                            {detail.in_stock_days}
                          </TableCell>
                          <TableCell>
                            <Badge className={getAgingRangeColor(detail.aging_range)}>
                              {detail.aging_range}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
};

export default AgingAnalysisPage;
