/**
 * 库存调整审批组件
 * 用于审批盘点差异并调整库存
 */

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, XCircle } from 'lucide-react';

interface AdjustmentApprovalProps {
  taskId: number;
  totalDifference: number;
  differenceCount: number;
  onApprove: (comment?: string) => Promise<void>;
  onReject: (comment: string) => Promise<void>;
}

const AdjustmentApproval: React.FC<AdjustmentApprovalProps> = ({
  taskId,
  totalDifference,
  differenceCount,
  onApprove,
  onReject,
}) => {
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);

  const handleApprove = async () => {
    if (!confirm('确定批准此盘点任务并调整库存吗？')) return;
    try {
      setLoading(true);
      await onApprove(comment);
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!comment.trim()) {
      alert('请填写拒绝原因');
      return;
    }
    if (!confirm('确定拒绝此盘点任务吗？')) return;
    try {
      setLoading(true);
      await onReject(comment);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>审批库存调整</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded">
          <div>
            <p className="text-sm text-gray-600">差异项目数</p>
            <p className="text-2xl font-bold text-orange-600">{differenceCount}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">差异总金额</p>
            <p
              className={`text-2xl font-bold ${
                totalDifference >= 0 ? 'text-green-600' : 'text-red-600'
              }`}
            >
              ¥{totalDifference >= 0 ? '+' : ''}
              {totalDifference.toFixed(2)}
            </p>
          </div>
        </div>

        <div>
          <Label>审批意见</Label>
          <Textarea
            placeholder="输入审批意见（可选）"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={3}
          />
        </div>

        <div className="flex gap-2">
          <Button
            onClick={handleApprove}
            disabled={loading}
            className="flex-1 bg-green-500 hover:bg-green-600"
          >
            <CheckCircle className="h-4 w-4 mr-2" />
            批准调整
          </Button>
          <Button
            onClick={handleReject}
            disabled={loading}
            variant="destructive"
            className="flex-1"
          >
            <XCircle className="h-4 w-4 mr-2" />
            拒绝
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default AdjustmentApproval;
