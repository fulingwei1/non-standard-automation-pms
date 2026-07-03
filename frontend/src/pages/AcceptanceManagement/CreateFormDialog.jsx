/**
 * Acceptance Management — create new acceptance record dialog
 */

import { useEffect, useState } from "react";

import {
  Button,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
  toast,
} from "../../components/ui";
import { acceptanceApi } from "../../services/api/acceptance";
import { projectApi } from "../../services/api/projects";

const unwrapItems = (response) => {
  const data = response?.data?.data ?? response?.data ?? response;
  if (Array.isArray(data)) return data;
  return data?.items || [];
};

// ── Inner form ───────────────────────────────────────────────────────────────

const CreateForm = ({ projects, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    project_id: "",
    machine_id: "",
    acceptance_type: "FAT",
    template_id: "",
    title: "",
    scheduled_date: "",
    location: "",
    customer_representative: "",
    our_representative: "",
    notes: "",
  });
  const [machines, setMachines] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loadingMachines, setLoadingMachines] = useState(false);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const set = (key, value) => setFormData((prev) => ({ ...prev, [key]: value }));
  const machineRequired = formData.acceptance_type !== "FINAL";

  useEffect(() => {
    setFormData((prev) => ({ ...prev, machine_id: "" }));
    setMachines([]);

    if (!formData.project_id || !machineRequired) {
      return;
    }

    let cancelled = false;
    setLoadingMachines(true);
    projectApi
      .getMachines(formData.project_id)
      .then((response) => {
        if (!cancelled) setMachines(unwrapItems(response));
      })
      .catch(() => {
        if (!cancelled) setMachines([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingMachines(false);
      });

    return () => {
      cancelled = true;
    };
  }, [formData.project_id, machineRequired]);

  useEffect(() => {
    setFormData((prev) => ({ ...prev, template_id: "" }));
    setTemplates([]);

    let cancelled = false;
    setLoadingTemplates(true);
    acceptanceApi.templates
      .list({ acceptance_type: formData.acceptance_type, page_size: 200 })
      .then((response) => {
        if (!cancelled) setTemplates(unwrapItems(response));
      })
      .catch(() => {
        if (!cancelled) setTemplates([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingTemplates(false);
      });

    return () => {
      cancelled = true;
    };
  }, [formData.acceptance_type]);

  const handleSubmit = async () => {
    if (!formData.project_id) {
      toast.warning("请选择项目");
      return;
    }
    if (machineRequired && !formData.machine_id) {
      toast.warning("请选择关联设备");
      return;
    }
    if (!formData.template_id) {
      toast.warning("请选择检查模板");
      return;
    }
    if (!formData.title) {
      toast.warning("请填写验收标题");
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit(formData);
    } catch (_err) {
      toast.error("创建失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        {/* 项目选择 */}
        <div className="space-y-2">
          <label className="text-sm text-slate-400">选择项目 *</label>
          <Select value={formData.project_id} onValueChange={(v) => set("project_id", v)}>
            <SelectTrigger aria-label="选择项目" className="bg-surface-100 border-white/10">
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
            <SelectTrigger aria-label="验收类型" className="bg-surface-100 border-white/10">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="FAT">FAT - 工厂验收测试</SelectItem>
              <SelectItem value="SAT">SAT - 现场验收测试</SelectItem>
              <SelectItem value="FINAL">终验收</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 设备选择 */}
        {machineRequired && (
          <div className="space-y-2">
            <label className="text-sm text-slate-400">关联设备 *</label>
            <Select
              value={formData.machine_id}
              onValueChange={(v) => set("machine_id", v)}
              disabled={!formData.project_id || loadingMachines || machines.length === 0}
            >
              <SelectTrigger aria-label="关联设备" className="bg-surface-100 border-white/10">
                <SelectValue
                  placeholder={
                    !formData.project_id
                      ? "先选择项目"
                      : loadingMachines
                        ? "加载设备..."
                        : machines.length === 0
                          ? "暂无设备"
                          : "选择设备"
                  }
                />
              </SelectTrigger>
              <SelectContent>
                {machines.map((machine) => (
                  <SelectItem key={machine.id} value={String(machine.id)}>
                    {machine.machine_name || machine.name || machine.machine_code || `设备${machine.id}`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {/* 检查模板 */}
        <div className="space-y-2">
          <label className="text-sm text-slate-400">检查模板 *</label>
          <Select
            value={formData.template_id}
            onValueChange={(v) => set("template_id", v)}
            disabled={loadingTemplates || templates.length === 0}
          >
            <SelectTrigger aria-label="检查模板" className="bg-surface-100 border-white/10">
              <SelectValue
                placeholder={
                  loadingTemplates
                    ? "加载模板..."
                    : templates.length === 0
                      ? "暂无模板"
                      : "选择模板"
                }
              />
            </SelectTrigger>
            <SelectContent>
              {templates.map((template) => (
                <SelectItem key={template.id} value={String(template.id)}>
                  {template.template_name || template.name || template.template_code}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* 验收标题 */}
        <div className="col-span-2 space-y-2">
          <label className="text-sm text-slate-400" htmlFor="acceptance-title">
            验收标题 *
          </label>
          <Input
            id="acceptance-title"
            aria-label="验收标题"
            value={formData.title}
            onChange={(e) => set("title", e.target.value)}
            placeholder="例如：XX 项目 FAT 验收"
            className="bg-surface-100 border-white/10"
          />
        </div>

        {/* 计划日期 */}
        <div className="space-y-2">
          <label className="text-sm text-slate-400" htmlFor="acceptance-scheduled-date">
            计划日期
          </label>
          <Input
            id="acceptance-scheduled-date"
            aria-label="计划日期"
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
