/**
 * ECN验证对话框 - 从ECNDetail.jsx安全提取
 *
 * 安全提取原则：
 * 1. 只接收必要的props
 * 2. 不持有内部状态，由父组件控制
 * 3. 通过回调函数与父组件通信
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select'

/**
 * @param {Object} props
 * @param {boolean} props.open - 是否打开对话框
 * @param {Function} props.onOpenChange - 打开状态变更回调
 * @param {Object} props.form - 表单数据 { verify_result, verify_note }
 * @param {Function} props.onFormChange - 表单变更回调
 * @param {Function} props.onSubmit - 提交回调
 */
export default function ECNVerifyDialog({
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
          <DialogTitle>验证ECN执行结果</DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <div>
            <label className="text-sm text-slate-500 mb-1 block">验证结果</label>
            <Select
              value={form.verify_result}
              onValueChange={(value) => onFormChange({ ...form, verify_result: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="PASS">通过</SelectItem>
                <SelectItem value="FAIL">不通过</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm text-slate-500 mb-1 block">验证说明</label>
            <Textarea
              value={form.verify_note}
              onChange={(e) => onFormChange({ ...form, verify_note: e.target.value })}
              placeholder="请输入验证说明"
            />
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit}>确认验证</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
