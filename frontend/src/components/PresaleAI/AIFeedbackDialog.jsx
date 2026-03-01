/**
 * AI反馈对话框组件
 * Team 10: 售前AI系统集成与前端UI
 */
import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Star } from 'lucide-react';
import { presaleAIService } from '@/services/presaleAIService';
import { toast } from 'sonner';

const AIFeedbackDialog = ({ open, onOpenChange, aiFunction, ticketId = null }) => {
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [feedbackText, setFeedbackText] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (rating === 0) {
      toast.error('请选择评分');
      return;
    }

    try {
      setSubmitting(true);
      await presaleAIService.submitFeedback({
        ai_function: aiFunction,
        presale_ticket_id: ticketId,
        rating: rating,
        feedback_text: feedbackText.trim() || null,
      });

      toast.success('反馈提交成功');
      onOpenChange(false);

      // 重置表单
      setRating(0);
      setFeedbackText('');
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      toast.error('反馈提交失败');
    } finally {
      setSubmitting(false);
    }
  };

  const getFunctionLabel = (func) => {
    const labels = {
      requirement: '需求理解',
      solution: '方案生成',
      cost: '成本估算',
      winrate: '赢率预测',
      quotation: '报价生成',
      knowledge: '知识库推荐',
      script: '话术助手',
      emotion: '情绪分析',
      mobile: '移动助手',
    };
    return labels[func] || func;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>AI功能反馈</DialogTitle>
          <DialogDescription>
            请为 <strong>{getFunctionLabel(aiFunction)}</strong> 功能打分并提供反馈
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Star Rating */}
          <div className="space-y-2">
            <label className="text-sm font-medium">评分</label>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setRating(star)}
                  onMouseEnter={() => setHoverRating(star)}
                  onMouseLeave={() => setHoverRating(0)}
                  className="transition-transform hover:scale-110"
                >
                  <Star
                    className={`h-8 w-8 ${
                      star <= (hoverRating || rating)
                        ? 'fill-yellow-400 text-yellow-400'
                        : 'text-gray-300'
                    }`}
                  />
                </button>
              ))}
            </div>
            <p className="text-sm text-muted-foreground">
              {rating === 0 && '请选择评分'}
              {rating === 1 && '非常不满意'}
              {rating === 2 && '不满意'}
              {rating === 3 && '一般'}
              {rating === 4 && '满意'}
              {rating === 5 && '非常满意'}
            </p>
          </div>

          {/* Feedback Text */}
          <div className="space-y-2">
            <label className="text-sm font-medium">详细反馈（可选）</label>
            <Textarea
              placeholder="请详细描述您的使用体验、遇到的问题或改进建议..."
              value={feedbackText || "unknown"}
              onChange={(e) => setFeedbackText(e.target.value)}
              rows={5}
              className="resize-none"
            />
            <p className="text-xs text-muted-foreground">
              {feedbackText.length}/500
            </p>
          </div>

          {/* Quick Feedback Options */}
          {rating > 0 && rating < 4 && (
            <div className="space-y-2">
              <label className="text-sm font-medium">常见问题（点击快速填充）</label>
              <div className="flex flex-wrap gap-2">
                {[
                  '响应速度慢',
                  '结果不准确',
                  '功能不够智能',
                  '界面不友好',
                  '缺少某些功能',
                ].map((issue) => (
                  <Button
                    key={issue}
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setFeedbackText((prev) =>
                        prev ? `${prev}\n- ${issue}` : `- ${issue}`
                      );
                    }}
                  >
                    {issue}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {rating >= 4 && (
            <div className="space-y-2">
              <label className="text-sm font-medium">您喜欢什么（点击快速填充）</label>
              <div className="flex flex-wrap gap-2">
                {[
                  '响应快速',
                  '结果准确',
                  '操作简单',
                  '功能实用',
                  '节省时间',
                ].map((strength) => (
                  <Button
                    key={strength}
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setFeedbackText((prev) =>
                        prev ? `${prev}\n- ${strength}` : `- ${strength}`
                      );
                    }}
                  >
                    {strength}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={submitting}
          >
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={submitting || rating === 0}>
            {submitting ? '提交中...' : '提交反馈'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default AIFeedbackDialog;
