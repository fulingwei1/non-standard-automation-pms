/**
 * RcaDialog Component
 * RCA 分析对话框
 */
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
  DialogDescription,
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

export default function RcaDialog({
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
          <DialogTitle>RCA分析（根本原因分析）</DialogTitle>
          <DialogDescription>
            分析ECN变更的根本原因，用于问题预防和质量改进
          </DialogDescription>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">
              根本原因类型
            </label>
            <Select
              value={form.root_cause}
              onValueChange={(value) =>
                setForm({ ...form, root_cause: value })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="选择根本原因类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="DESIGN_ERROR">设计问题</SelectItem>
                <SelectItem value="MATERIAL_DEFECT">物料缺陷</SelectItem>
                <SelectItem value="PROCESS_ERROR">工艺问题</SelectItem>
                <SelectItem value="EXTERNAL_FACTOR">外部因素</SelectItem>
                <SelectItem value="COMMUNICATION">沟通问题</SelectItem>
                <SelectItem value="PLANNING">计划问题</SelectItem>
                <SelectItem value="OTHER">其他</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">原因分类</label>
            <Input
              value={form.root_cause_category}
              onChange={(e) =>
                setForm({ ...form, root_cause_category: e.target.value })
              }
              placeholder="如：设计缺陷、工艺不当、物料问题等"
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">
              RCA分析内容 *
            </label>
            <Textarea
              value={form.root_cause_analysis}
              onChange={(e) =>
                setForm({ ...form, root_cause_analysis: e.target.value })
              }
              placeholder="详细分析变更的根本原因，包括：&#10;1. 问题描述&#10;2. 根本原因分析&#10;3. 为什么发生&#10;4. 如何预防"
              rows={10}
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
