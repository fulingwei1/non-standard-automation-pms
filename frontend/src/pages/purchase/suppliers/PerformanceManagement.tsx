/**
 * 供应商绩效管理页
 * @page PerformanceManagement
 * @description 管理和查看供应商绩效评估
 */

import React, { useState, useEffect } from 'react';
import { RefreshCw, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { useToast } from '../../../hooks/use-toast';
import purchaseService from '../../../services/purchase/purchaseService';
import type { SupplierPerformance } from '../../../types/purchase';
import PerformanceScoreCard from './components/PerformanceScoreCard';

const PerformanceManagement: React.FC = () => {
  const { toast } = useToast();
  const [performances, setPerformances] = useState<SupplierPerformance[]>([]);
  const [loading, setLoading] = useState(false);
  const [period, setPeriod] = useState(new Date().toISOString().substring(0, 7)); // YYYY-MM
  const [supplierId, setSupplierId] = useState<number>(1); // 示例供应商ID

  const loadPerformances = async () => {
    setLoading(true);
    try {
      const data = await purchaseService.getSupplierPerformance(supplierId, {
        evaluation_period: period,
      });
      setPerformances(data);
    } catch (error: any) {
      toast({
        title: '加载失败',
        description: error.response?.data?.detail || '无法加载绩效数据',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPerformances();
  }, [period, supplierId]);

  const handleEvaluate = async () => {
    setLoading(true);
    try {
      await purchaseService.evaluateSupplier(supplierId, {
        supplier_id: supplierId,
        evaluation_period: period,
      });
      toast({
        title: '评估成功',
        description: '供应商绩效评估已完成',
      });
      loadPerformances();
    } catch (error: any) {
      toast({
        title: '评估失败',
        description: error.response?.data?.detail || '无法触发评估',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-2xl font-bold flex items-center gap-2">
              <TrendingUp className="h-6 w-6" />
              供应商绩效管理
            </CardTitle>
            <div className="flex gap-2">
              <Input
                type="month"
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                className="w-48"
              />
              <Button onClick={handleEvaluate} disabled={loading}>
                触发评估
              </Button>
              <Button onClick={loadPerformances} disabled={loading} variant="outline">
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {loading && performances.length === 0 ? (
            <div className="text-center py-12">
              <RefreshCw className="animate-spin h-8 w-8 mx-auto mb-4 text-gray-400" />
              <p className="text-gray-500">加载中...</p>
            </div>
          ) : performances.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">暂无绩效数据</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6">
              {performances.map((perf) => (
                <PerformanceScoreCard key={perf.id} performance={perf} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default PerformanceManagement;
