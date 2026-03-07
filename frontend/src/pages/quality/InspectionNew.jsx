/**
 * 新建检验任务
 * 调用 POST /production/quality/inspection
 */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { FileCheck, ArrowLeft, Save, Loader2 } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { qualityApi } from "../../services/api/quality";

const INSPECTION_TYPES = [
  { value: "IQC", label: "来料检验 (IQC)" },
  { value: "IPQC", label: "过程检验 (IPQC)" },
  { value: "FQC", label: "成品检验 (FQC)" },
  { value: "OQC", label: "出货检验 (OQC)" },
];

function FormField({ label, required, children, error }) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium text-text-secondary">
        {label} {required && <span className="text-red-400">*</span>}
      </label>
      {children}
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}

export default function InspectionNew() {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [form, setForm] = useState({
    inspection_type: "IQC",
    work_order_id: "",
    material_id: "",
    inspection_qty: "",
    qualified_qty: "",
    defect_qty: "",
    measured_value: "",
    remark: "",
  });

  const inputCls = "w-full px-3 py-2 rounded-lg bg-surface-300 border border-white/5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-violet-500";

  const updateField = (field, value) => setForm((prev) => ({ ...prev, [field]: value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        inspection_type: form.inspection_type,
        inspection_qty: parseInt(form.inspection_qty) || 0,
        qualified_qty: parseInt(form.qualified_qty) || 0,
        defect_qty: parseInt(form.defect_qty) || 0,
      };
      if (form.work_order_id) payload.work_order_id = parseInt(form.work_order_id);
      if (form.material_id) payload.material_id = parseInt(form.material_id);
      if (form.measured_value) payload.measured_value = parseFloat(form.measured_value);
      if (form.remark) payload.remark = form.remark;

      await qualityApi.inspection.create(payload);
      navigate("/quality/inspections");
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "创建失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader
        title="新建检验"
        subtitle="创建新的检验任务"
        icon={<FileCheck className="h-6 w-6" />}
        actions={
          <Button variant="ghost" onClick={() => navigate(-1)} className="gap-2">
            <ArrowLeft className="h-4 w-4" /> 返回
          </Button>
        }
      />

      <main className="container mx-auto px-4 py-6 max-w-3xl">
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-4 text-red-400 text-sm">
            {error}
          </div>
        )}

        <motion.form
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          onSubmit={handleSubmit}
          className="bg-surface-200 rounded-xl border border-white/5 p-6 space-y-6"
        >
          <h3 className="text-lg font-semibold text-text-primary">检验信息</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField label="检验类型" required>
              <select
                value={form.inspection_type}
                onChange={(e) => updateField("inspection_type", e.target.value)}
                className={inputCls}
              >
                {INSPECTION_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </FormField>

            <FormField label="工单ID">
              <input
                type="number"
                placeholder="关联工单ID（可选）"
                value={form.work_order_id}
                onChange={(e) => updateField("work_order_id", e.target.value)}
                className={inputCls}
              />
            </FormField>

            <FormField label="物料ID">
              <input
                type="number"
                placeholder="关联物料ID（可选）"
                value={form.material_id}
                onChange={(e) => updateField("material_id", e.target.value)}
                className={inputCls}
              />
            </FormField>

            <FormField label="送检数量" required>
              <input
                type="number"
                placeholder="输入送检数量"
                value={form.inspection_qty}
                onChange={(e) => updateField("inspection_qty", e.target.value)}
                className={inputCls}
                required
                min="1"
              />
            </FormField>

            <FormField label="合格数量" required>
              <input
                type="number"
                placeholder="输入合格数量"
                value={form.qualified_qty}
                onChange={(e) => updateField("qualified_qty", e.target.value)}
                className={inputCls}
                required
                min="0"
              />
            </FormField>

            <FormField label="不良数量">
              <input
                type="number"
                placeholder="输入不良数量"
                value={form.defect_qty}
                onChange={(e) => updateField("defect_qty", e.target.value)}
                className={inputCls}
                min="0"
              />
            </FormField>

            <FormField label="测量值">
              <input
                type="number"
                step="any"
                placeholder="SPC测量值（可选）"
                value={form.measured_value}
                onChange={(e) => updateField("measured_value", e.target.value)}
                className={inputCls}
              />
            </FormField>
          </div>

          <FormField label="备注">
            <textarea
              rows={3}
              placeholder="备注信息..."
              value={form.remark}
              onChange={(e) => updateField("remark", e.target.value)}
              className={inputCls}
            />
          </FormField>

          <div className="flex justify-end gap-3 pt-4 border-t border-white/5">
            <Button variant="ghost" type="button" onClick={() => navigate(-1)}>取消</Button>
            <Button type="submit" disabled={submitting} className="gap-2">
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              {submitting ? "提交中..." : "提交"}
            </Button>
          </div>
        </motion.form>
      </main>
    </div>
  );
}
