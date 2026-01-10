/**
 * ECN关闭对话框 - 从ECNDetail.jsx安全提取
 */
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from '../../components/ui/dialog'
import { Button } from '../../components/ui/button'
import { Textarea } from '../../components/ui/textarea'

/**
 * @param {Object} props
 * @param {boolean} props.open - 是否打开对话框
 * @param {Function} props.onOpenChange - 打开状态变更回调
 * @param {Object} props.form - 表单数据 { close_note }
 * @param {Function} props.onFormChange - 表单变更回调
 * @param {Function} props.onSubmit - 提交回调
 */
export default function ECNCloseDialog({
  open,
  onOpenChange,
  form,
  onFormChange,
  onSubmit,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>关闭ECN</DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <div>
            <label className="text-sm text-slate-500 mb-1 block">关闭说明</label>
            <Textarea
              value={form.close_note}
              onChange={(e) => onFormChange({ ...form, close_note: e.target.value })}
              placeholder="请输入关闭说明"
            />
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit}>确认关闭</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
