import { useState } from "react";
import { X } from "lucide-react";

const MachineForm = ({
  isOpen,
  onClose,
  onSubmit,
  initialData = {},
  projectId,
}) => {
  const [formData, setFormData] = useState({
    machine_code: "",
    machine_name: "",
    machine_no: 1,
    machine_type: "",
    specification: "",
    planned_start_date: "",
    planned_end_date: "",
    progress_pct: 0,
    health: "H1",
    remark: "",
    ...initialData,
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]:
        name === "progress_pct" || name === "machine_no"
          ? Number(value)
          : value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ ...formData, project_id: projectId });
  };

  if (!isOpen) {return null;}

  return (
    <div className="modal-overlay">
      <div
        className="glass-panel modal-content animate-fade"
        style={{ maxWidth: "600px", width: "90%", padding: "0" }}
      >
        <div
          style={{
            padding: "20px 24px",
            borderBottom: "1px solid var(--border-color)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <h2 style={{ fontSize: "1.25rem", fontWeight: 600 }}>
            {initialData.id ? "编辑设备" : "添加设备"}
          </h2>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              color: "var(--text-dim)",
              cursor: "pointer",
            }}
          >
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: "24px" }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "20px",
            }}
          >
            <div>
              <label className="form-label">设备编码 *</label>
              <input
                name="machine_code"
                value={formData.machine_code}
                onChange={handleChange}
                className="form-input"
                placeholder="如: M-001"
                required
                disabled={!!initialData.id}
              />
            </div>
            <div>
              <label className="form-label">设备名称 *</label>
              <input
                name="machine_name"
                value={formData.machine_name}
                onChange={handleChange}
                className="form-input"
                placeholder="如: 自动装配工位"
                required
              />
            </div>
            <div>
              <label className="form-label">设备类型</label>
              <input
                name="machine_type"
                value={formData.machine_type}
                onChange={handleChange}
                className="form-input"
                placeholder="如: 机械/电气/混合"
              />
            </div>
            <div>
              <label className="form-label">设备规格</label>
              <input
                name="specification"
                value={formData.specification}
                onChange={handleChange}
                className="form-input"
                placeholder="尺寸、功率等"
              />
            </div>
            <div>
              <label className="form-label">计划开始</label>
              <input
                type="date"
                name="planned_start_date"
                value={formData.planned_start_date}
                onChange={handleChange}
                className="form-input"
              />
            </div>
            <div>
              <label className="form-label">计划结束</label>
              <input
                type="date"
                name="planned_end_date"
                value={formData.planned_end_date}
                onChange={handleChange}
                className="form-input"
              />
            </div>
            <div>
              <label className="form-label">健康度</label>
              <select
                name="health"
                value={formData.health}
                onChange={handleChange}
                className="form-input"
              >
                <option value="H0">H0 - 停止</option>
                <option value="H1">H1 - 正常</option>
                <option value="H2">H2 - 预警</option>
                <option value="H3">H3 - 严重</option>
              </select>
            </div>
            <div>
              <label className="form-label">完成进度 (%)</label>
              <input
                type="number"
                name="progress_pct"
                value={formData.progress_pct}
                onChange={handleChange}
                min="0"
                max="100"
                className="form-input"
              />
            </div>
          </div>

          <div style={{ marginTop: "20px" }}>
            <label className="form-label">备注</label>
            <textarea
              name="remark"
              value={formData.remark}
              onChange={handleChange}
              className="form-input"
              style={{ height: "80px", resize: "none" }}
            />
          </div>

          <div
            style={{
              marginTop: "32px",
              display: "flex",
              gap: "12px",
              justifyContent: "flex-end",
            }}
          >
            <button
              type="button"
              onClick={onClose}
              className="nav-item"
              style={{ background: "rgba(255,255,255,0.05)" }}
            >
              取消
            </button>
            <button type="submit" className="btn-primary">
              保存设备
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MachineForm;
