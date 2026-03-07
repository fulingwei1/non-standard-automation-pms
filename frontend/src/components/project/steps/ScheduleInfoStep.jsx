import { Input, FormTextarea } from "../../ui";
import { Calendar } from "lucide-react";

/**
 * 时间节点步骤组件
 */
export const ScheduleInfoStep = ({ formData, setFormData }) => {
  const calculateDays = () => {
    if (formData.planned_start_date && formData.planned_end_date) {
      const start = new Date(formData.planned_start_date);
      const end = new Date(formData.planned_end_date);
      return Math.ceil((end - start) / (1000 * 60 * 60 * 24));
    }
    return null;
  };

  const days = calculateDays();

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">
            计划开始日期
          </label>
          <Input
            type="date"
            value={formData.planned_start_date}
            onChange={(e) =>
              setFormData({
                ...formData,
                planned_start_date: e.target.value,
              })
            }
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">
            计划结束日期
          </label>
          <Input
            type="date"
            value={formData.planned_end_date}
            onChange={(e) =>
              setFormData({
                ...formData,
                planned_end_date: e.target.value,
              })
            }
            min={formData.planned_start_date}
          />
        </div>
      </div>

      {days !== null && (
        <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
          <div className="flex items-center gap-2 text-sm text-amber-300">
            <Calendar className="h-4 w-4" />
            <span>项目周期：{days} 天</span>
          </div>
        </div>
      )}

      <FormTextarea
        label="项目需求摘要"
        name="requirements"
        value={formData.requirements}
        onChange={(e) =>
          setFormData({ ...formData, requirements: e.target.value })
        }
        placeholder="请输入项目需求摘要（可选）"
        rows={4}
      />
    </div>
  );
};
