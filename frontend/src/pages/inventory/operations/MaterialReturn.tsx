/**
 * 退料入库页面
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, PackagePlus } from 'lucide-react';
import OperationForm from './components/OperationForm';
import InventoryAPI from '@/services/inventory';
import { ReturnRequest } from '@/types/inventory';

const MaterialReturn: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (data: ReturnRequest) => {
    try {
      setLoading(true);
      setSuccess(false);
      await InventoryAPI.returnMaterial(data);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (error: any) {
      console.error('退料失败:', error);
      alert(`退料失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <PackagePlus className="h-8 w-8 text-green-500" />
          退料入库
        </h1>
        <p className="text-gray-500 mt-1">生产车间退回多余物料</p>
      </div>

      {success && (
        <Alert className="bg-green-50 border-green-200">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            退料成功！库存已更新。
          </AlertDescription>
        </Alert>
      )}

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>填写退料信息</CardTitle>
        </CardHeader>
        <CardContent>
          <OperationForm type="return" onSubmit={handleSubmit} loading={loading} />
        </CardContent>
      </Card>
    </div>
  );
};

export default MaterialReturn;
