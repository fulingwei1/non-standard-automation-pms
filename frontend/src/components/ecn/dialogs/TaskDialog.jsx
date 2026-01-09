/**
 * TaskDialog Component
 * 创建 ECN 执行任务对话框
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

export default function TaskDialog({
  open,
  onOpenChange,
  form,
  setForm,
  onSubmit,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>创建执行任务</DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">任务名称 *</label>
            <Input
              value={form.task_name}
              onChange={(e) =>
                setForm({ ...form, task_name: e.target.value })
              }
              placeholder="请输入任务名称"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">任务类型</label>
              <Select
                value={form.task_type}
                onValueChange={(value) =>
                  setForm({ ...form, task_type: value })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择任务类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="BOM_UPDATE">BOM更新</SelectItem>
                  <SelectItem value="DRAWING_UPDATE">图纸更新</SelectItem>
                  <SelectItem value="PROGRAM_UPDATE">程序更新</SelectItem>
                  <SelectItem value="PURCHASE_ADJUST">采购调整</SelectItem>
                  <SelectItem value="OTHER">其他</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">责任部门</label>
              <Input
                value={form.task_dept}
                onChange={(e) =>
                  setForm({ ...form, task_dept: e.target.value })
                }
                placeholder="如：机械部、电气部等"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">任务描述</label>
            <Textarea
              value={form.task_description}
              onChange={(e) =>
                setForm({ ...form, task_description: e.target.value })
              }
              placeholder="详细描述任务内容和要求"
              rows={4}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                计划开始日期
              </label>
              <Input
                type="date"
                value={form.planned_start}
                onChange={(e) =>
                  setForm({ ...form, planned_start: e.target.value })
                }
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">
                计划结束日期
              </label>
              <Input
                type="date"
                value={form.planned_end}
                onChange={(e) =>
                  setForm({ ...form, planned_end: e.target.value })
                }
              />
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit}>创建任务</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
