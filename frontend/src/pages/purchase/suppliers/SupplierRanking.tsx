/**
 * 供应商排名页
 * @page SupplierRanking
 */

import React, { useState, useEffect } from 'react';
import { Trophy, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Badge } from '../../../components/ui/badge';
import { useToast } from '../../../hooks/use-toast';
import purchaseService from '../../../services/purchase/purchaseService';
import type { SupplierRankingResponse } from '../../../types/purchase';
import RankingTable from './components/RankingTable';

const SupplierRanking: React.FC = () => {
  const { toast } = useToast();
  const [rankingData, setRankingData] = useState<SupplierRankingResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [period, setPeriod] = useState(new Date().toISOString().substring(0, 7));

  const loadRankings = async () => {
    setLoading(true);
    try {
      const data = await purchaseService.getSupplierRanking({
        evaluation_period: period,
      });
      setRankingData(data);
    } catch (error: any) {
      toast({
        title: '加载失败',
        description: error.response?.data?.detail || '无法加载排名数据',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRankings();
  }, [period]);

  return (
    <div className="container mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-2xl font-bold flex items-center gap-2">
              <Trophy className="h-6 w-6 text-yellow-600" />
              供应商排名
            </CardTitle>
            <div className="flex gap-2">
              <Input
                type="month"
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                className="w-48"
              />
              <Button onClick={loadRankings} disabled={loading} variant="outline">
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {rankingData && (
            <div className="mb-4 flex gap-4">
              <Badge variant="outline">
                评估期间: {rankingData.evaluation_period}
              </Badge>
              <Badge variant="outline">
                供应商总数: {rankingData.total_suppliers}
              </Badge>
            </div>
          )}

          {loading && !rankingData ? (
            <div className="text-center py-12">
              <RefreshCw className="animate-spin h-8 w-8 mx-auto mb-4 text-gray-400" />
              <p className="text-gray-500">加载中...</p>
            </div>
          ) : !rankingData ? (
            <div className="text-center py-12">
              <p className="text-gray-500">暂无排名数据</p>
            </div>
          ) : (
            <RankingTable rankings={rankingData.rankings} />
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default SupplierRanking;
