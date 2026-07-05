/**
 * KPI 表单组件
 */
import { useState } from "react";
import {
  Input,
  Button,
  DialogFooter,
} from "../../components/ui";
import { BSC_DIMENSIONS } from "../../lib/constants/strategy";
import { COLLECTION_FREQUENCY } from "./constants";

export default function KPIForm({ kpi, onSubmit, onCancel, loading }) {
  const [formData, setFormData] = useState({
    name: kpi?.name || "",
    description: kpi?.description || "",
    target_value: kpi?.target_value || 100,
    current_value: kpi?.current_value || 0,
    unit: kpi?.unit || "%",
    collection_frequency: kpi?.collection_frequency || "MONTHLY",
    dimension: kpi?.dimension || "FINANCIAL",
    csf_id: kpi?.csf_id || "",
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            KPI 名称 *
          </label>
          <Input
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="输入 KPI 名称"
            required
            className="bg-slate-800/50 border-slate-700"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            描述
          </label>
          <textarea
            value={formData.description}
            onChange={(e) =>
              setFormData({ ...formData, description: e.target.value })
            }
            placeholder="描述该 KPI 指标"
            rows={2}
            className="w-full rounded-lg bg-slate-800/50 border border-slate-700 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              目标值 *
            </label>
            <Input
              type="number"
              step="0.01"
              value={formData.target_value}
              onChange={(e) =>
                setFormData({ ...formData, target_value: e.target.value })
              }
              className="bg-slate-800/50 border-slate-700"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              当前值
            </label>
            <Input
              type="number"
              step="0.01"
              value={formData.current_value}
              onChange={(e) =>
                setFormData({ ...formData, current_value: e.target.value })
              }
              className="bg-slate-800/50 border-slate-700"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              单位
            </label>
            <Input
              value={formData.unit}
              onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
              placeholder="%"
              className="bg-slate-800/50 border-slate-700"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              BSC 维度 *
            </label>
            <select
              value={formData.dimension}
              onChange={(e) =>
                setFormData({ ...formData, dimension: e.target.value })
              }
              className="w-full rounded-lg bg-slate-800/50 border border-slate-700 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/50"
              required
            >
              {Object.entries(BSC_DIMENSIONS).map(([key, config]) => (
                <option key={key} value={key}>
                  {config.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              采集频率 *
            </label>
            <select
              value={formData.collection_frequency}
              onChange={(e) =>
                setFormData({ ...formData, collection_frequency: e.target.value })
              }
              className="w-full rounded-lg bg-slate-800/50 border border-slate-700 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/50"
              required
            >
              {Object.entries(COLLECTION_FREQUENCY).map(([key, config]) => (
                <option key={key} value={key}>
                  {config.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <DialogFooter className="mt-6">
        <Button type="button" variant="outline" onClick={onCancel}>
          取消
        </Button>
        <Button type="submit" disabled={loading}>
          {loading ? "保存中..." : kpi?.id ? "更新" : "创建"}
        </Button>
      </DialogFooter>
    </form>
  );
}
