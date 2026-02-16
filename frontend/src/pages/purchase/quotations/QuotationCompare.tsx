/**
 * 报价比价页
 * @page QuotationCompare
 */

import React, { useState } from 'react';
import { DollarSign, Search } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { useToast } from '../../../hooks/use-toast';
import purchaseService from '../../../services/purchase/purchaseService';
import type { QuotationCompareResponse } from '../../../types/purchase';
import CompareTable from './components/CompareTable';

const QuotationCompare: React.FC = () => {
  const { toast } = useToast();
  const [compareData, setCompareData] = useState<QuotationCompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [materialId, setMaterialId] = useState('');

  const handleCompare = async () => {
    if (!materialId) {
      toast({
        title: '请输入物料ID',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    try {
      const data = await purchaseService.compareQuotations({
        material_id: parseInt(materialId),
      });
      setCompareData(data);
    } catch (error: any) {
      toast({
        title: '比价失败',
        description: error.response?.data?.detail || '无法获取报价比较',
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
          <CardTitle className="text-2xl font-bold flex items-center gap-2">
            <DollarSign className="h-6 w-6" />
            报价比价
          </CardTitle>
        </CardHeader>

        <CardContent>
          <div className="flex gap-2 mb-6">
            <Input
              placeholder="输入物料ID"
              value={materialId}
              onChange={(e) => setMaterialId(e.target.value)}
              type="number"
            />
            <Button onClick={handleCompare} disabled={loading}>
              <Search className="h-4 w-4 mr-2" />
              比价
            </Button>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <p className="text-gray-500">加载中...</p>
            </div>
          ) : !compareData ? (
            <div className="text-center py-12">
              <p className="text-gray-500">请输入物料ID进行比价</p>
            </div>
          ) : (
            <CompareTable compareData={compareData} />
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default QuotationCompare;
