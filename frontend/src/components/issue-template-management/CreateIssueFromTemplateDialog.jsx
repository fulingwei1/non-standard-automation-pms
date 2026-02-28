import React from "react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";

export default function CreateIssueFromTemplateDialog({
  open,
  onOpenChange,
  template,
  form,
  setForm,
  projects,
  machines,
  onConfirm,
}) {
  const handleChange = (key, value) => {
    setForm({ ...form, [key]: value });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-surface-50 border-white/10 max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-white">从模板创建问题</DialogTitle>
        </DialogHeader>
        {template && (
          <div className="space-y-4">
            <div className="p-3 bg-surface-100 rounded border border-white/10">
              <p className="text-sm text-slate-400">
                模板：{template.template_name}
              </p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">关联项目</Label>
                <Select
                  value={form.project_id}
                  onValueChange={(value) => {
                    setForm({
                      ...form,
                      project_id: value,
                      machine_id: "",
                    });
                  }}
                >
                  <SelectTrigger className="bg-surface-100 border-white/10 text-white">
                    <SelectValue placeholder="选择项目" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">不关联</SelectItem>
                    {(projects || []).map((project) => (
                      <SelectItem
                        key={project.id}
                        value={project.id.toString()}
                      >
                        {project.project_name} ({project.project_code})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-slate-300">关联机台</Label>
                <Select
                  value={form.machine_id}
                  onValueChange={(value) => handleChange("machine_id", value)}
                  disabled={!form.project_id}
                >
                  <SelectTrigger
                    className="bg-surface-100 border-white/10 text-white"
                    disabled={!form.project_id}
                  >
                    <SelectValue
                      placeholder={
                        form.project_id ? "选择机台" : "请先选择项目"
                      }
                    />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">不关联</SelectItem>
                    {(machines || []).map((machine) => (
                      <SelectItem
                        key={machine.id}
                        value={machine.id.toString()}
                      >
                        {machine.machine_name} ({machine.machine_code})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label className="text-slate-300">要求完成日期</Label>
              <Input
                type="date"
                value={form.due_date}
                onChange={(e) => handleChange("due_date", e.target.value)}
                className="bg-surface-100 border-white/10 text-white"
              />
            </div>
            <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded">
              <p className="text-sm text-blue-300">
                提示：标题和描述将使用模板的默认值，您可以在创建后编辑。
              </p>
            </div>
          </div>
        )}
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="border-white/10 text-slate-300"
          >
            取消
          </Button>
          <Button onClick={onConfirm} className="bg-primary hover:bg-primary/90">
            创建问题
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
