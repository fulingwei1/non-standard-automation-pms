/**
 * OrderDialog Component
 * 受影响订单对话框
 */
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from '../../ui/dialog'
import { Button } from '../../ui/button'
import { Input } from '../../ui/input'
import { Textarea } from '../../ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../ui/select'

export default function OrderDialog({
  open,
  onOpenChange,
  form,
  setForm,
  onSubmit,
  editingOrder,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {editingOrder ? '编辑受影响订单' : '添加受影响订单'}
          </DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">订单类型 *</label>
            <Select
              value={form.order_type}
              onValueChange={(value) =>
                setForm({ ...form, order_type: value, order_id: null, order_no: '' })
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="PURCHASE">采购订单</SelectItem>
                <SelectItem value="OUTSOURCING">外协订单</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">订单号 *</label>
            <Input
              value={form.order_no}
              onChange={(e) => setForm({ ...form, order_no: e.target.value })}
              placeholder="请输入订单号"
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">影响描述</label>
            <Textarea
              value={form.impact_description}
              onChange={(e) =>
                setForm({ ...form, impact_description: e.target.value })
              }
              placeholder="描述ECN对订单的影响"
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">处理方式</label>
            <Select
              value={form.action_type}
              onValueChange={(value) =>
                setForm({ ...form, action_type: value })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="选择处理方式" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="CANCEL">取消订单</SelectItem>
                <SelectItem value="MODIFY">修改订单</SelectItem>
                <SelectItem value="ADD">新增订单</SelectItem>
                <SelectItem value="DELAY">延期订单</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">处理说明</label>
            <Textarea
              value={form.action_description}
              onChange={(e) =>
                setForm({ ...form, action_description: e.target.value })
              }
              placeholder="请输入处理说明"
            />
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit}>保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
