import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
  Button,
  Input,
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "../../components/ui";
import { DEFAULT_FORM_DATA } from "./constants";

const toOptionalNumber = (value) => {
  if (value === "" || value === null || value === undefined) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : value;
};

export function RdProjectFormDialog({ open, onOpenChange, onSubmit, categories = [] }) {
  const [formData, setFormData] = useState(DEFAULT_FORM_DATA);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const submitData = {
        ...formData,
        category_id: toOptionalNumber(formData.category_id),
        budget_amount: formData.budget_amount
          ? parseFloat(formData.budget_amount)
          : null,
        project_manager_id: toOptionalNumber(formData.project_manager_id),
        linked_project_id: toOptionalNumber(formData.linked_project_id),
        initiation_date: formData.initiation_date || null,
        planned_start_date: formData.planned_start_date || null,
        planned_end_date: formData.planned_end_date || null,
      };
      await onSubmit(submitData);
      setFormData(DEFAULT_FORM_DATA);
      onOpenChange(false);
    } catch (err) {
      console.error("Failed to create project:", err);
    } finally {
      setLoading(false);
    }
  };

  const textareaClass =
    "w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>创建研发项目</DialogTitle>
          <DialogDescription>录入研发立项、预算和研究目标，用于后续费用归集与报表。</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <DialogBody className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  项目名称 <span className="text-red-500">*</span>
                </label>
                <Input
                  value={formData.project_name}
                  onChange={(e) =>
                    setFormData({ ...formData, project_name: e.target.value })
                  }
                  placeholder="请输入项目名称"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  项目分类
                </label>
                <Select
                  value={formData.category_id?.toString() || "__none__"}
                  onValueChange={(value) =>
                    setFormData({
                      ...formData,
                      category_id:
                        value && value !== "__none__" ? parseInt(value) : "",
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="请选择分类" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">请选择分类</SelectItem>
                    {(categories || []).map((cat) => (
                      <SelectItem key={cat.id} value={cat.id.toString()}>
                        {cat.category_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  项目类型 <span className="text-red-500">*</span>
                </label>
                <Select
                  value={formData.category_type}
                  onValueChange={(value) =>
                    setFormData({ ...formData, category_type: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="请选择类型" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="SELF">自主研发</SelectItem>
                    <SelectItem value="ENTRUST">委托研发</SelectItem>
                    <SelectItem value="COOPERATION">合作研发</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  立项日期
                </label>
                <Input
                  type="date"
                  value={formData.initiation_date}
                  onChange={(e) =>
                    setFormData({ ...formData, initiation_date: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
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
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
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
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  预算金额
                </label>
                <Input
                  type="number"
                  step="0.01"
                  value={formData.budget_amount}
                  onChange={(e) =>
                    setFormData({ ...formData, budget_amount: e.target.value })
                  }
                  placeholder="0.00"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                立项原因
              </label>
              <textarea
                className={textareaClass}
                rows={2}
                value={formData.initiation_reason}
                onChange={(e) =>
                  setFormData({ ...formData, initiation_reason: e.target.value })
                }
                placeholder="请输入立项原因"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                研究目标
              </label>
              <textarea
                className={textareaClass}
                rows={2}
                value={formData.research_goal}
                onChange={(e) =>
                  setFormData({ ...formData, research_goal: e.target.value })
                }
                placeholder="请输入研究目标"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                研究内容
              </label>
              <textarea
                className={textareaClass}
                rows={3}
                value={formData.research_content}
                onChange={(e) =>
                  setFormData({ ...formData, research_content: e.target.value })
                }
                placeholder="请输入研究内容"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                预期结果
              </label>
              <textarea
                className={textareaClass}
                rows={2}
                value={formData.expected_result}
                onChange={(e) =>
                  setFormData({ ...formData, expected_result: e.target.value })
                }
                placeholder="请输入预期结果"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                备注
              </label>
              <textarea
                className={textareaClass}
                rows={2}
                value={formData.remark}
                onChange={(e) =>
                  setFormData({ ...formData, remark: e.target.value })
                }
                placeholder="请输入备注"
              />
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={() => onOpenChange(false)}
            >
              取消
            </Button>
            <Button type="submit" loading={loading}>
              创建项目
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
