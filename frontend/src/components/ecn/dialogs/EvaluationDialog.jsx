/**
 * EvaluationDialog Component
 * 创建 ECN 评估对话框
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

export default function EvaluationDialog({
  open,
  onOpenChange,
  form,
  setForm,
  onSubmit,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>创建部门评估</DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">
              评估部门 *
            </label>
            <Input
              value={form.eval_dept}
              onChange={(e) =>
                setForm({ ...form, eval_dept: e.target.value })
              }
              placeholder="如：机械部、电气部、软件部等"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">成本估算</label>
              <Input
                type="number"
                value={form.cost_estimate}
                onChange={(e) =>
                  setForm({
                    ...form,
                    cost_estimate: parseFloat(e.target.value) || 0,
                  })
                }
                placeholder="0"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">工期估算（天）</label>
              <Input
                type="number"
                value={form.schedule_estimate}
                onChange={(e) =>
                  setForm({
                    ...form,
                    schedule_estimate: parseInt(e.target.value) || 0,
                  })
                }
                placeholder="0"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">影响分析 *</label>
            <Textarea
              value={form.impact_analysis}
              onChange={(e) =>
                setForm({ ...form, impact_analysis: e.target.value })
              }
              placeholder="详细分析变更对本部门的影响"
              rows={4}
            />
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">资源需求</label>
            <Textarea
              value={form.resource_requirement}
              onChange={(e) =>
                setForm({ ...form, resource_requirement: e.target.value })
              }
              placeholder="执行变更所需的人力、设备等资源"
              rows={3}
            />
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">风险评估</label>
            <Textarea
              value={form.risk_assessment}
              onChange={(e) =>
                setForm({ ...form, risk_assessment: e.target.value })
              }
              placeholder="评估变更可能带来的风险和应对措施"
              rows={3}
            />
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">评估结果</label>
            <Select
              value={form.eval_result}
              onValueChange={(value) =>
                setForm({ ...form, eval_result: value })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="选择评估结果" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="APPROVED">通过</SelectItem>
                <SelectItem value="CONDITIONAL">有条件通过</SelectItem>
                <SelectItem value="REJECTED">不通过</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">评估意见</label>
            <Textarea
              value={form.eval_opinion}
              onChange={(e) =>
                setForm({ ...form, eval_opinion: e.target.value })
              }
              placeholder="填写评估意见和说明"
              rows={3}
            />
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">附加条件</label>
            <Textarea
              value={form.conditions}
              onChange={(e) =>
                setForm({ ...form, conditions: e.target.value })
              }
              placeholder="执行变更需要满足的条件"
              rows={2}
            />
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit}>创建评估</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
