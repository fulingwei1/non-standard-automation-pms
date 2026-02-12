/**
 * 进度报工对话框组件
 */
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogBody } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Slider } from '../ui/slider';
import { QUICK_QUANTITY_OPTIONS } from '@/lib/constants/workerWorkstation';
import { calculateProgress } from '@/lib/constants/workerWorkstation';

/**
 * 进度报工对话框
 * @param {object} props
 * @param {boolean} props.open - 是否打开
 * @param {function} props.onOpenChange - 打开状态改变回调
 * @param {object} props.order - 工单数据
 * @param {object} props.data - 表单数据
 * @param {function} props.onChange - 数据改变回调
 * @param {function} props.onConfirm - 确认回调
 * @param {boolean} props.submitting - 提交中
 */
export default function ProgressReportDialog({
  open,
  onOpenChange,
  order,
  data,
  onChange,
  onConfirm,
  submitting
}) {
  const _progress = calculateProgress(data?.progress_percent || 0, order?.plan_qty || 0);

  const handleQuickQuantity = (value) => {
    const planQty = order?.plan_qty || 0;
    const qty = value === 'all' ? planQty : value;
    const newProgress = calculateProgress(qty, planQty);
    onChange && onChange({
      ...data,
      progress_percent: newProgress,
      completed_qty: qty
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-slate-900 border-slate-700 text-white max-w-md">
        <DialogHeader>
          <DialogTitle>进度报工</DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          {/* 工单信息 */}
          <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
            <div className="text-sm text-slate-400 mb-1">工单信息</div>
            <div className="text-white font-medium">{order?.work_order_no || order?.code}</div>
            <div className="flex items-center justify-between text-sm text-slate-400 mt-1">
              <span>计划: {order?.plan_qty || 0}</span>
              <span>已完成: {data?.completed_qty || order?.completed_qty || 0}</span>
            </div>
          </div>

          {/* 快捷数量选择 */}
          <div>
            <Label className="text-white mb-2 block">快捷选择完成数量</Label>
            <div className="grid grid-cols-4 gap-2">
              {QUICK_QUANTITY_OPTIONS.map((option) =>
              <Button
                key={option.value}
                variant="outline"
                size="sm"
                onClick={() => handleQuickQuantity(option.value)}
                className="bg-slate-800/50 border-slate-700/50 hover:bg-slate-700/50">

                  {option.label}
              </Button>
              )}
            </div>
          </div>

          {/* 进度滑块 */}
          <div>
            <Label className="text-white mb-2 block">完成进度: {data?.progress_percent || 0}%</Label>
            <Slider
              value={[data?.progress_percent || 0]}
              onValueChange={([value]) =>
              onChange && onChange({
                ...data,
                progress_percent: value,
                completed_qty: Math.round(value / 100 * (order?.plan_qty || 0))
              })
              }
              max={100}
              step={1}
              className="py-2" />

          </div>

          {/* 进度备注 */}
          <div>
            <Label htmlFor="progress_note" className="text-white">进度备注</Label>
            <Textarea
              id="progress_note"
              value={data?.progress_note || ''}
              onChange={(e) => onChange && onChange({ ...data, progress_note: e.target.value })}
              placeholder="填写进度情况（可选）"
              className="mt-1 bg-slate-800/50 border-slate-700/50 min-h-[80px]" />

          </div>

          {/* 当前问题 */}
          <div>
            <Label htmlFor="current_issues" className="text-white">当前问题</Label>
            <Textarea
              id="current_issues"
              value={data?.current_issues || ''}
              onChange={(e) => onChange && onChange({ ...data, current_issues: e.target.value })}
              placeholder="记录遇到的问题（可选）"
              className="mt-1 bg-slate-800/50 border-slate-700/50 min-h-[80px]" />

          </div>
        </DialogBody>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange && onOpenChange(false)}
            disabled={submitting}>

            取消
          </Button>
          <Button
            onClick={onConfirm}
            disabled={submitting || !data?.progress_percent || data?.progress_percent === 0}>

            {submitting ? '提交中...' : '确认提交'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>);

}