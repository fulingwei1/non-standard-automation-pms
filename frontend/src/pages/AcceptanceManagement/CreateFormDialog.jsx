/**
 * Acceptance Management — create new acceptance record dialog
 */

import { useState } from "react";

import {
  toast,
} from "../../components/ui";

// ── Inner form ───────────────────────────────────────────────────────────────

const CreateForm = ({ projects, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    project_id: "",
    acceptance_type: "FAT",
    title: "",
    scheduled_date: "",
    location: "",
    customer_representative: "",
    our_representative: "",
    notes: "",
  });
  const [submitting, setSubmitting] = useState(false);

  const set = (key, value) => setFormData((prev) => ({ ...prev, [key]: value }));

  const handleSubmit = async () => {
    if (!formData.project_id) {
      toast({ title: "警告", description: "请选择项目", variant: "destructive" });
      return;
    }
    if (!formData.title) {
      toast({ title: "警告", description: "请填写验收标题", variant: "destructive" });
      return;
    }

    setSubmitting(true);
    await onSubmit(formData);
    setSubmitting(false);
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        {/* 项目选择 */}
        <div className="space-y-2">
          <label className="text-sm text-slate-400">选择项目 *</label>
          <Select value={formData.project_id} onValueChange={(v) => set("project_id", v)}>
            <SelectTrigger className="bg-surface-100 border-white/10">
              <SelectValue placeholder="选择项目" />
            </SelectTrigger>
            <SelectContent>
              {projects.map((p) => (
                <SelectItem key={p.id} value={String(p.id)}>
                  {p.project_name || p.project_code}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* 验收类型 */}
        <div className="space-y-2">
          <label className="text-sm text-slate-400">验收类型 *</label>
          <Select value={formData.acceptance_type} onValueChange={(v) => set("acceptance_type", v)}>
            <SelectTrigger className="bg-surface-100 border-white/10">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="FAT">FAT - 工厂验收测试</SelectItem>
              <SelectItem value="SAT">SAT - 现场验收测试</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 验收标题 */}
        <div className="col-span-2 space-y-2">
          <label className="text-sm text-slate-400">验收标题 *</label>
          <Input
            value={formData.title}
            onChange={(e) => set("title", e.target.value)}
            placeholder="例如：XX 项目 FAT 验收"
            className="bg-surface-100 border-white/10"
          />
        </div>

        {/* 计划日期 */}
        <div className="space-y-2">
          <label className="text-sm text-slate-400">计划日期</label>
          <Input
            type="date"
            value={formData.scheduled_date}
            onChange={(e) => set("scheduled_date", e.target.value)}
            className="bg-surface-100 border-white/10"
          />
        </div>

        {/* 验收地点 */}
        <div className="space-y-2">
          <label className="text-sm text-slate-400">验收地点</label>
          <Input
            value={formData.location}
            onChange={(e) => set("location", e.target.value)}
            placeholder="例如：公司装配车间"
            className="bg-surface-100 border-white/10"
          />
        </div>

        {/* 客户代表 */}
        <div className="space-y-2">
          <label className="text-sm text-slate-400">客户代表</label>
          <Input
            value={formData.customer_representative}
            onChange={(e) => set("customer_representative", e.target.value)}
            placeholder="客户方负责人"
            className="bg-surface-100 border-white/10"
          />
        </div>

        {/* 我方代表 */}
        <div className="space-y-2">
          <label className="text-sm text-slate-400">我方代表</label>
          <Input
            value={formData.our_representative}
            onChange={(e) => set("our_representative", e.target.value)}
            placeholder="我方负责人"
            className="bg-surface-100 border-white/10"
          />
        </div>

        {/* 备注 */}
        <div className="col-span-2 space-y-2">
          <label className="text-sm text-slate-400">备注</label>
          <textarea
            rows={3}
            value={formData.notes}
            onChange={(e) => set("notes", e.target.value)}
            placeholder="备注信息"
            className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary resize-none"
          />
        </div>
      </div>

      <DialogFooter>
        <Button variant="outline" onClick={onCancel}>
          取消
        </Button>
        <Button onClick={handleSubmit} disabled={submitting}>
          {submitting ? "创建中..." : "创建"}
        </Button>
      </DialogFooter>
    </div>
  );
};

// ── Dialog wrapper ───────────────────────────────────────────────────────────

const CreateFormDialog = ({ open, onOpenChange, projects, onSubmit }) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>新建验收记录</DialogTitle>
          <DialogDescription>创建新的 FAT/SAT 验收记录</DialogDescription>
        </DialogHeader>
        <CreateForm
          projects={projects}
          onSubmit={onSubmit}
          onCancel={() => onOpenChange(false)}
        />
      </DialogContent>
    </Dialog>
  );
};

export default CreateFormDialog;
