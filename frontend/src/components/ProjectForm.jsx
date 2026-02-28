import React, { useState, useEffect } from "react";
import { X } from "lucide-react";
import { customerApi, orgApi } from "../services/api";

const ProjectForm = ({ isOpen, onClose, onSubmit, initialData = {} }) => {
  const [formData, setFormData] = useState({
    project_code: "",
    project_name: "",
    short_name: "",
    customer_id: "",
    contract_no: "",
    project_type: "FIXED_PRICE",
    contract_date: "",
    planned_start_date: "",
    planned_end_date: "",
    contract_amount: 0,
    budget_amount: 0,
    pm_id: "",
    description: "",
    ...initialData,
  });

  const [customers, setCustomers] = useState([]);
  const [employees, setEmployees] = useState([]);

  useEffect(() => {
    if (isOpen) {
      const loadOptions = async () => {
        try {
          const [custRes, empRes] = await Promise.all([
            customerApi.list(),
            orgApi.employees(),
          ]);
          setCustomers(custRes.data);
          setEmployees(empRes.data);
        } catch (err) {
          console.error("Failed to load form options:", err);
        }
      };
      loadOptions();
    }
  }, [isOpen]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]:
        name.includes("amount") || name.includes("_id")
          ? value === ""
            ? ""
            : Number(value)
          : value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  if (!isOpen) {return null;}

  return (
    <div className="modal-overlay">
      <div
        className="glass-panel modal-content animate-fade"
        style={{ maxWidth: "800px", width: "90%", padding: "0" }}
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
            {initialData.id ? "编辑项目" : "新建项目"}
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
              <label className="form-label">项目编码 *</label>
              <input
                name="project_code"
                value={formData.project_code}
                onChange={handleChange}
                className="form-input"
                placeholder="例如: PROJ-2024-001"
                required
                disabled={!!initialData.id}
              />
            </div>
            <div>
              <label className="form-label">项目名称 *</label>
              <input
                name="project_name"
                value={formData.project_name}
                onChange={handleChange}
                className="form-input"
                placeholder="项目全称"
                required
              />
            </div>
            <div>
              <label className="form-label">客户 *</label>
              <select
                name="customer_id"
                value={formData.customer_id}
                onChange={handleChange}
                className="form-input"
                required
              >
                <option value="">选择客户</option>
                {(customers || []).map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.customer_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="form-label">项目经理 (PM)</label>
              <select
                name="pm_id"
                value={formData.pm_id}
                onChange={handleChange}
                className="form-input"
              >
                <option value="">选择 PM</option>
                {(employees || []).map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.name} ({e.employee_code})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="form-label">合同编号</label>
              <input
                name="contract_no"
                value={formData.contract_no}
                onChange={handleChange}
                className="form-input"
              />
            </div>
            <div>
              <label className="form-label">计划开始日期</label>
              <input
                type="date"
                name="planned_start_date"
                value={formData.planned_start_date}
                onChange={handleChange}
                className="form-input"
              />
            </div>
            <div>
              <label className="form-label">计划交付日期</label>
              <input
                type="date"
                name="planned_end_date"
                value={formData.planned_end_date}
                onChange={handleChange}
                className="form-input"
              />
            </div>
            <div>
              <label className="form-label">项目预算 (CNY)</label>
              <input
                type="number"
                name="budget_amount"
                value={formData.budget_amount}
                onChange={handleChange}
                className="form-input"
              />
            </div>
          </div>

          <div style={{ marginTop: "20px" }}>
            <label className="form-label">项目描述</label>
            <textarea
              name="description"
              value={formData.description}
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
              保存项目
            </button>
          </div>
        </form>
      </div>

      <style>
        {`
                .modal-overlay {
                    position: fixed;
                    inset: 0;
                    background: rgba(0, 0, 0, 0.4);
                    backdrop-filter: blur(8px);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                    padding: 20px;
                }
                .modal-content {
                    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
                }
                .form-label {
                    display: block;
                    font-size: 0.85rem;
                    color: var(--text-dim);
                    margin-bottom: 8px;
                }
                .form-input {
                    width: 100%;
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    padding: 10px 14px;
                    color: white;
                    outline: none;
                    transition: border-color 0.2s;
                }
                .form-input:focus {
                    border-color: var(--primary-color);
                }
                .form-input:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
            `}
      </style>
    </div>
  );
};

export default ProjectForm;
