import React from "react";
import { Input, FormSelect } from "../../ui";
import { Info } from "lucide-react";

/**
 * 财务信息步骤组件
 */
export const FinanceInfoStep = ({
  formData,
  setFormData,
  employees = [],
  pmStats = {},
}) => {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">
            合同金额 (CNY)
          </label>
          <Input
            type="number"
            value={formData.contract_amount}
            onChange={(e) =>
              setFormData({
                ...formData,
                contract_amount: parseFloat(e.target.value) || 0,
              })
            }
            placeholder="0.00"
            min="0"
            step="0.01"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">
            预算金额 (CNY)
          </label>
          <Input
            type="number"
            value={formData.budget_amount}
            onChange={(e) =>
              setFormData({
                ...formData,
                budget_amount: parseFloat(e.target.value) || 0,
              })
            }
            placeholder="0.00"
            min="0"
            step="0.01"
          />
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-300">合同日期</label>
        <Input
          type="date"
          value={formData.contract_date}
          onChange={(e) =>
            setFormData({ ...formData, contract_date: e.target.value })
          }
        />
      </div>

      <FormSelect
        label="项目经理 (PM)"
        name="pm_id"
        value={formData.pm_id}
        onChange={(e) => {
          const pmId = e.target.value;
          const pm = (employees || []).find((e) => e.id === parseInt(pmId));
          setFormData({
            ...formData,
            pm_id: pmId,
            pm_name: pm ? pm.name || pm.real_name : "",
          });
        }}
      >
        <option value="">选择项目经理（可选）</option>
        {(employees || []).map((emp) => {
          const projectCount = pmStats[emp.id] || 0;
          return (
            <option key={emp.id} value={emp.id}>
              {emp.name || emp.real_name} ({emp.employee_code})
              {projectCount > 0 && ` - ${projectCount}个项目`}
            </option>
          );
        })}
      </FormSelect>

      {formData.pm_id && (
        <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-blue-300">
              <Info className="h-4 w-4" />
              <span>项目经理信息将自动填充</span>
            </div>
            {pmStats[formData.pm_id] !== undefined && (
              <div className="text-xs text-blue-200/80 ml-6">
                当前负责项目数: {pmStats[formData.pm_id]} 个
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
