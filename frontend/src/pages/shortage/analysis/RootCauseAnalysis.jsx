/**
 * 根因分析页面
 * Team 3 - Root Cause Analysis
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { getRootCauseAnalysis } from '@/services/api/shortage';
import RootCauseBarChart from './components/RootCauseBarChart';
import { Badge } from '@/components/ui/badge';
import { Lightbulb, AlertTriangle } from 'lucide-react';
import { toast } from '@/hooks/use-toast';

const RootCauseAnalysis = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);

  // 加载根因数据
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const response = await getRootCauseAnalysis();
        setData(response.data);
      } catch (error) {
        console.error('Failed to load root cause data:', error);
        toast({
          title: '加载失败',
          description: error.message,
          variant: 'destructive',
        });
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="p-6 space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">根因分析</h1>
        <p className="text-gray-500 mt-1">
          识别缺料根本原因，优化管理流程
        </p>
      </div>

      {/* 根因分布图表 */}
      <RootCauseBarChart data={data.root_causes || []} />

      {/* 成本影响分析 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-500" />
            成本影响分析
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {data.root_causes?.map((item, index) => {
              const costImpact = parseFloat(item.cost_impact || 0);
              const percentage = item.percentage || 0;
              
              return (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Badge variant="outline">{item.label}</Badge>
                    <span className="text-sm text-gray-600">
                      占比: {percentage.toFixed(1)}%
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-500">累计成本影响</p>
                    <p className="text-xl font-bold text-orange-600">
                      ¥{costImpact.toLocaleString()}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* 改进建议 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-yellow-500" />
            改进建议
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {data.recommendations?.map((rec, index) => (
              <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                <h4 className="font-semibold text-gray-900 mb-1">
                  {rec.title}
                </h4>
                <p className="text-sm text-gray-600">{rec.description}</p>
                {rec.priority && (
                  <Badge
                    variant={rec.priority === 'HIGH' ? 'destructive' : 'secondary'}
                    className="mt-2"
                  >
                    {rec.priority === 'HIGH' ? '高优先级' : '普通'}
                  </Badge>
                )}
              </div>
            )) || (
              <div className="space-y-4">
                <div className="border-l-4 border-red-500 pl-4 py-2">
                  <h4 className="font-semibold text-gray-900 mb-1">
                    优化需求预测准确性
                  </h4>
                  <p className="text-sm text-gray-600">
                    建议使用AI预测引擎，结合历史数据和季节性因素，提高预测准确率至90%以上。
                  </p>
                  <Badge variant="destructive" className="mt-2">
                    高优先级
                  </Badge>
                </div>

                <div className="border-l-4 border-orange-500 pl-4 py-2">
                  <h4 className="font-semibold text-gray-900 mb-1">
                    加强供应商管理
                  </h4>
                  <p className="text-sm text-gray-600">
                    建立供应商评级体系，定期评估交期准时率。对延期频繁的供应商进行约谈或更换。
                  </p>
                  <Badge variant="destructive" className="mt-2">
                    高优先级
                  </Badge>
                </div>

                <div className="border-l-4 border-blue-500 pl-4 py-2">
                  <h4 className="font-semibold text-gray-900 mb-1">
                    建立质量预警机制
                  </h4>
                  <p className="text-sm text-gray-600">
                    对来料质量实施全检或抽检，建立不良品退货快速通道，减少因质量问题导致的缺料。
                  </p>
                  <Badge variant="secondary" className="mt-2">
                    普通
                  </Badge>
                </div>

                <div className="border-l-4 border-green-500 pl-4 py-2">
                  <h4 className="font-semibold text-gray-900 mb-1">
                    规范紧急插单流程
                  </h4>
                  <p className="text-sm text-gray-600">
                    制定紧急订单审批流程，评估对现有项目的影响。考虑设置安全库存应对突发需求。
                  </p>
                  <Badge variant="secondary" className="mt-2">
                    普通
                  </Badge>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default RootCauseAnalysis;
