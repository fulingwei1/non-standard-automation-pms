/**
 * 完工报工对话框组件
 */
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogBody } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { QUICK_QUANTITY_OPTIONS } from './workerWorkstationConstants';

/**
 * 完工报工对话框
 * @param {object} props
 * @param {boolean} props.open - 是否打开
 * @param {function} props.onOpenChange - 打开状态改变回调
 * @param {object} props.order - 工单数据
 * @param {object} props.data - 表单数据
 * @param {function} props.onChange - 数据改变回调
 * @param {function} props.onConfirm - 确认回调
 * @param {boolean} props.submitting - 提交中
 */
export default function CompleteWorkDialog({
  open,
  onOpenChange,
  order,
  data,
  onChange,
  onConfirm,
  submitting,
}) {
  const defectQty = (data?.completed_qty || 0) - (data?.qualified_qty || 0);

  const handleQuickQuantity = (value) => {
    const planQty = order?.plan_qty || 0;
    const qty = value === 'all' ? planQty : value;
    onChange && onChange({
      ...data,
      completed_qty: qty,
      qualified_qty: qty,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-slate-900 border-slate-700 text-white max-w-md">
        <DialogHeader>
          <DialogTitle>完工报工</DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          {/* 工单信息 */}
          <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
            <div className="text-sm text-slate-400 mb-1">工单信息</div>
            <div className="text-white font-medium">{order?.work_order_no || order?.code}</div>
            <div className="text-sm text-slate-400">计划数量: {order?.plan_qty || 0}</div>
          </div>

          {/* 快捷数量选择 */}
          <div>
            <Label className="text-white mb-2 block">快捷选择完成数量</Label>
            <div className="grid grid-cols-4 gap-2">
              {QUICK_QUANTITY_OPTIONS.map((option) => (
                <Button
                  key={option.value}
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickQuantity(option.value)}
                  className="bg-slate-800/50 border-slate-700/50 hover:bg-slate-700/50"
                >
                  {option.label}
                </Button>
              ))}
            </div>
          </div>

          {/* 完成数量 */}
          <div>
            <Label htmlFor="completed_qty" className="text-white">完成数量</Label>
            <Input
              id="completed_qty"
              type="number"
              value={data?.completed_qty || ''}
              onChange={(e) => {
                const qty = parseInt(e.target.value) || 0;
                onChange && onChange({
                  ...data,
                  completed_qty: qty,
                  qualified_qty: data?.qualified_qty ? Math.min(data.qualified_qty, qty) : qty,
                });
              }}
              placeholder="输入完成数量"
              className="mt-1 bg-slate-800/50 border-slate-700/50"
            />
          </div>

          {/* 合格数量 */}
          <div>
            <Label htmlFor="qualified_qty" className="text-white">合格数量</Label>
            <Input
              id="qualified_qty"
              type="number"
              value={data?.qualified_qty || ''}
              onChange={(e) =>
                onChange && onChange({ ...data, qualified_qty: parseInt(e.target.value) || 0 })
              }
              placeholder="输入合格数量"
              className="mt-1 bg-slate-800/50 border-slate-700/50"
            />
            {defectQty > 0 && (
              <div className="text-sm text-amber-400 mt-1">
                次品数量: {defectQty}
              </div>
            )}
          </div>

          {/* 工作工时 */}
          <div>
            <Label htmlFor="work_hours" className="text-white">工作工时（小时）</Label>
            <Input
              id="work_hours"
              type="number"
              step="0.5"
              value={data?.work_hours || ''}
              onChange={(e) =>
                onChange && onChange({ ...data, work_hours: parseFloat(e.target.value) || 0 })
              }
              placeholder="输入实际工作工时"
              className="mt-1 bg-slate-800/50 border-slate-700/50"
            />
          </div>

          {/* 完工备注 */}
          <div>
            <Label htmlFor="report_note" className="text-white">完工备注</Label>
            <Textarea
              id="report_note"
              value={data?.report_note || ''}
              onChange={(e) => onChange && onChange({ ...data, report_note: e.target.value })}
              placeholder="填写完工情况（可选）"
              className="mt-1 bg-slate-800/50 border-slate-700/50 min-h-[80px]"
            />
          </div>
        </DialogBody>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange && onOpenChange(false)}
            disabled={submitting}
          >
            取消
          </Button>
          <Button
            onClick={onConfirm}
            disabled={
              submitting ||
              !data?.completed_qty ||
              data?.completed_qty <= 0 ||
              !data?.qualified_qty ||
              data?.qualified_qty <= 0
            }
          >
            {submitting ? '提交中...' : '确认完工'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
