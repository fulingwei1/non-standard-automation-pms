/**
 * SolutionTemplateDialog Component
 * 创建解决方案模板对话框
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

export default function SolutionTemplateDialog({
  open,
  onOpenChange,
  form,
  setForm,
  onSubmit,
  ecn,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>创建解决方案模板</DialogTitle>
          <DialogDescription>
            从当前ECN创建可复用的解决方案模板
          </DialogDescription>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">模板名称 *</label>
            <Input
              value={form.template_name}
              onChange={(e) =>
                setForm({ ...form, template_name: e.target.value })
              }
              placeholder="输入模板名称"
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">模板分类</label>
            <Input
              value={form.template_category}
              onChange={(e) =>
                setForm({ ...form, template_category: e.target.value })
              }
              placeholder="如：设计变更、物料变更等"
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">
              关键词（用逗号分隔）
            </label>
            <Input
              value={form.keywords.join(', ')}
              onChange={(e) => {
                const keywords = e.target.value
                  .split(',')
                  .map((k) => k.trim())
                  .filter((k) => k)
                setForm({ ...form, keywords })
              }}
              placeholder="输入关键词，用逗号分隔"
            />
          </div>
          {ecn?.solution && (
            <div>
              <label className="text-sm font-medium mb-2 block">解决方案内容</label>
              <div className="p-3 bg-slate-50 rounded text-sm whitespace-pre-wrap">
                {ecn.solution}
              </div>
            </div>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit}>创建模板</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
