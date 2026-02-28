/**
 * 开工报工对话框组件
 */
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogBody } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Checkbox } from '../ui/checkbox';

/**
 * 开工报工对话框
 * @param {object} props
 * @param {boolean} props.open - 是否打开
 * @param {function} props.onOpenChange - 打开状态改变回调
 * @param {object} props.order - 工单数据
 * @param {object} props.data - 表单数据
 * @param {function} props.onChange - 数据改变回调
 * @param {function} props.onConfirm - 确认回调
 * @param {boolean} props.submitting - 提交中
 */
export default function StartWorkDialog({
  open,
  onOpenChange,
  order,
  data,
  onChange,
  onConfirm,
  submitting,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-slate-900 border-slate-700 text-white max-w-md">
        <DialogHeader>
          <DialogTitle>开工报工</DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          {/* 工单信息 */}
          <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
            <div className="text-sm text-slate-400 mb-1">工单信息</div>
            <div className="text-white font-medium">{order?.work_order_no || order?.code}</div>
            <div className="text-sm text-slate-400">{order?.project_name}</div>
          </div>

          {/* 设备检查 */}
          <div className="flex items-center gap-3">
            <Checkbox
              id="equipment_check"
              checked={data?.equipment_check}
              onCheckedChange={(checked) =>
                onChange && onChange({ ...data, equipment_check: checked })
              }
            />
            <Label htmlFor="equipment_check" className="text-white cursor-pointer">
              我已检查设备状态，确认可以正常工作
            </Label>
          </div>

          {/* 物料检查 */}
          <div className="flex items-center gap-3">
            <Checkbox
              id="material_check"
              checked={data?.material_check}
              onCheckedChange={(checked) =>
                onChange && onChange({ ...data, material_check: checked })
              }
            />
            <Label htmlFor="material_check" className="text-white cursor-pointer">
              我已确认所需物料已准备齐全
            </Label>
          </div>

          {/* 开工备注 */}
          <div>
            <Label htmlFor="start_note" className="text-white">开工备注</Label>
            <Input
              id="start_note"
              value={data?.start_note || ''}
              onChange={(e) => onChange && onChange({ ...data, start_note: e.target.value })}
              placeholder="填写开工备注（可选）"
              className="mt-1 bg-slate-800/50 border-slate-700/50"
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
            disabled={submitting || !data?.equipment_check || !data?.material_check}
          >
            {submitting ? '提交中...' : '确认开工'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
