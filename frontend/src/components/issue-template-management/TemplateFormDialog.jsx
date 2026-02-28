import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../ui/dialog";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";

export default function TemplateFormDialog({
  open,
  onOpenChange,
  form,
  setForm,
  tagInput,
  setTagInput,
  onSubmit,
  isEdit,
  categoryConfigs,
  issueTypeConfigs,
  severityConfigs,
  priorityConfigs,
}) {
  const handleChange = (key, value) => {
    setForm({ ...form, [key]: value });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-surface-50 border-white/10 max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-white">
            {isEdit ? "编辑模板" : "新建模板"}
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-slate-300">模板名称 *</Label>
              <Input
                value={form.template_name}
                onChange={(e) => handleChange("template_name", e.target.value)}
                className="bg-surface-100 border-white/10 text-white"
                placeholder="例如：温度控制问题模板"
              />
            </div>
            <div>
              <Label className="text-slate-300">模板编码 *</Label>
              <Input
                value={form.template_code}
                onChange={(e) => handleChange("template_code", e.target.value)}
                className="bg-surface-100 border-white/10 text-white"
                placeholder="例如：TEMP_CTRL_001"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-slate-300">分类</Label>
              <Select
                value={form.category}
                onValueChange={(value) => handleChange("category", value)}
              >
                <SelectTrigger className="bg-surface-100 border-white/10 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(categoryConfigs).map(([key, config]) => (
                    <SelectItem key={key} value={key}>
                      {config.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-slate-300">问题类型</Label>
              <Select
                value={form.issue_type}
                onValueChange={(value) => handleChange("issue_type", value)}
              >
                <SelectTrigger className="bg-surface-100 border-white/10 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(issueTypeConfigs).map(([key, config]) => (
                    <SelectItem key={key} value={key}>
                      {config.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-slate-300">默认严重程度</Label>
              <Select
                value={form.default_severity}
                onValueChange={(value) => handleChange("default_severity", value)}
              >
                <SelectTrigger className="bg-surface-100 border-white/10 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(severityConfigs).map(([key, config]) => (
                    <SelectItem key={key} value={key}>
                      {config.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-slate-300">默认优先级</Label>
              <Select
                value={form.default_priority}
                onValueChange={(value) => handleChange("default_priority", value)}
              >
                <SelectTrigger className="bg-surface-100 border-white/10 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(priorityConfigs).map(([key, config]) => (
                    <SelectItem key={key} value={key}>
                      {config.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label className="text-slate-300">标题模板 *</Label>
            <Input
              value={form.title_template}
              onChange={(e) => handleChange("title_template", e.target.value)}
              className="bg-surface-100 border-white/10 text-white"
              placeholder="例如：{project_name} - 温度控制问题"
            />
            <p className="text-xs text-slate-400 mt-1">
              支持变量：{"{project_name}"}, {"{machine_code}"}, {"{date}"}
            </p>
          </div>

          <div>
            <Label className="text-slate-300">描述模板</Label>
            <Textarea
              value={form.description_template}
              onChange={(e) =>
                handleChange("description_template", e.target.value)
              }
              className="bg-surface-100 border-white/10 text-white"
              rows={4}
              placeholder="例如：项目 {project_code} 在 {date} 发现温度控制问题..."
            />
          </div>

          <div>
            <Label className="text-slate-300">解决方案模板</Label>
            <Textarea
              value={form.solution_template}
              onChange={(e) => handleChange("solution_template", e.target.value)}
              className="bg-surface-100 border-white/10 text-white"
              rows={3}
              placeholder="解决方案描述..."
            />
          </div>

          <div>
            <Label className="text-slate-300">默认标签（逗号分隔）</Label>
            <Input
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              className="bg-surface-100 border-white/10 text-white"
              placeholder="例如：温度控制,FAT"
            />
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_blocking"
                checked={form.default_is_blocking}
                onChange={(e) =>
                  handleChange("default_is_blocking", e.target.checked)
                }
                className="w-4 h-4"
              />
              <Label
                htmlFor="is_blocking"
                className="text-slate-300 cursor-pointer"
              >
                默认是否阻塞
              </Label>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active"
                checked={form.is_active}
                onChange={(e) => handleChange("is_active", e.target.checked)}
                className="w-4 h-4"
              />
              <Label
                htmlFor="is_active"
                className="text-slate-300 cursor-pointer"
              >
                启用
              </Label>
            </div>
          </div>

          <div>
            <Label className="text-slate-300">备注</Label>
            <Textarea
              value={form.remark}
              onChange={(e) => handleChange("remark", e.target.value)}
              className="bg-surface-100 border-white/10 text-white"
              rows={2}
              placeholder="备注说明..."
            />
          </div>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="border-white/10 text-slate-300"
          >
            取消
          </Button>
          <Button onClick={onSubmit} className="bg-primary hover:bg-primary/90">
            保存
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
