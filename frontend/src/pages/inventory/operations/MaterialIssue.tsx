/**
 * 领料出库页面
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, PackageMinus } from 'lucide-react';
import OperationForm from './components/OperationForm';
import InventoryAPI from '@/services/inventory';
import { IssueRequest } from '@/types/inventory';

const MaterialIssue: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (data: IssueRequest) => {
    try {
      setLoading(true);
      setSuccess(false);
      await InventoryAPI.issueMaterial(data);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (error: any) {
      console.error('领料失败:', error);
      alert(`领料失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <PackageMinus className="h-8 w-8 text-red-500" />
          领料出库
        </h1>
        <p className="text-gray-500 mt-1">生产车间领取物料</p>
      </div>

      {success && (
        <Alert className="bg-green-50 border-green-200">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            领料成功！库存已更新。
          </AlertDescription>
        </Alert>
      )}

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>填写领料信息</CardTitle>
        </CardHeader>
        <CardContent>
          <OperationForm type="issue" onSubmit={handleSubmit} loading={loading} />
        </CardContent>
      </Card>
    </div>
  );
};

export default MaterialIssue;
