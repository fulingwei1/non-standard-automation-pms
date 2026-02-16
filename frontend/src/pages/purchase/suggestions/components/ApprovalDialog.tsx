/**
 * 采购建议批准对话框
 * @component ApprovalDialog
 * @description 用于批准或拒绝采购建议
 */

import React, { useState } from 'react';
import { CheckCircle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../../../components/ui/dialog';
import { Button } from '../../../../components/ui/button';
import { Textarea } from '../../../../components/ui/textarea';
import { Label } from '../../../../components/ui/label';
import { useToast } from '../../../../hooks/use-toast';
import purchaseService from '../../../../services/purchase/purchaseService';
import type { PurchaseSuggestion } from '../../../../types/purchase';

interface ApprovalDialogProps {
  open: boolean;
  suggestion: PurchaseSuggestion;
  onClose: () => void;
  onSuccess: () => void;
}

const ApprovalDialog: React.FC<ApprovalDialogProps> = ({
  open,
  suggestion,
  onClose,
  onSuccess,
}) => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [reviewNote, setReviewNote] = useState('');

  /**
   * 提交批准
   */
  const handleSubmit = async () => {
    setLoading(true);
    try {
      await purchaseService.approveSuggestion(suggestion.id, {
        approved: true,
        review_note: reviewNote || '批准',
      });

      toast({
        title: '操作成功',
        description: `采购建议 ${suggestion.suggestion_no} 已批准`,
      });

      onSuccess();
    } catch (error: any) {
      toast({
        title: '操作失败',
        description: error.response?.data?.detail || '无法批准采购建议',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-600" />
            批准采购建议
          </DialogTitle>
          <DialogDescription>
            请确认以下采购建议信息，并添加审批意见
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* 建议信息 */}
          <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="text-sm text-gray-500">建议编号</p>
              <p className="font-medium">{suggestion.suggestion_no}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">物料</p>
              <p className="font-medium">{suggestion.material_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">采购数量</p>
              <p className="font-medium">
                {suggestion.suggested_qty} {suggestion.unit}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">推荐供应商</p>
              <p className="font-medium">{suggestion.suggested_supplier_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">预估单价</p>
              <p className="font-medium">¥{suggestion.estimated_unit_price.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">预估总额</p>
              <p className="font-medium text-blue-600">
                ¥{suggestion.estimated_total_amount.toFixed(2)}
              </p>
            </div>
          </div>

          {/* AI 推荐信息 */}
          <div className="p-4 bg-blue-50 rounded-lg">
            <p className="text-sm font-medium text-blue-900 mb-2">AI 推荐理由</p>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-600">综合评分：</span>
                <span className="font-medium">{suggestion.recommendation_reason.total_score.toFixed(1)}</span>
              </div>
              <div>
                <span className="text-gray-600">绩效得分：</span>
                <span className="font-medium">{suggestion.recommendation_reason.performance_score.toFixed(1)}</span>
              </div>
              <div>
                <span className="text-gray-600">价格得分：</span>
                <span className="font-medium">{suggestion.recommendation_reason.price_score.toFixed(1)}</span>
              </div>
              <div>
                <span className="text-gray-600">交期得分：</span>
                <span className="font-medium">{suggestion.recommendation_reason.delivery_score.toFixed(1)}</span>
              </div>
            </div>
            <div className="mt-2">
              <span className="text-sm text-gray-600">AI 置信度：</span>
              <span className={`text-sm font-medium ml-2 ${
                suggestion.ai_confidence >= 80 ? 'text-green-600' :
                suggestion.ai_confidence >= 60 ? 'text-yellow-600' :
                'text-red-600'
              }`}>
                {suggestion.ai_confidence.toFixed(1)}%
              </span>
            </div>
          </div>

          {/* 审批意见 */}
          <div className="space-y-2">
            <Label htmlFor="review-note">审批意见（可选）</Label>
            <Textarea
              id="review-note"
              placeholder="请输入审批意见..."
              value={reviewNote}
              onChange={(e) => setReviewNote(e.target.value)}
              rows={4}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={loading}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? '处理中...' : '确认批准'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ApprovalDialog;
