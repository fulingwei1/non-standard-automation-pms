/**
 * 制定应对计划对话框
 */

import { useState } from "react";
import { Button, Dialog, DialogBody, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "../ui";



export default function ResponseRiskDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    response_strategy: "",
    response_plan: "",
    owner_id: "",
  });

  const handleSubmit = () => {
    if (!formData.response_strategy.trim() || !formData.response_plan.trim()) {
      alert("请填写应对策略和应对措施");
      return;
    }
    onSubmit(formData);
    setFormData({ response_strategy: "", response_plan: "", owner_id: "" });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>制定应对计划</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                应对策略 <span className="text-red-400">*</span>
              </label>
              <select
                value={formData.response_strategy}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    response_strategy: e.target.value,
                  })
                }
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">请选择</option>
                <option value="AVOID">规避</option>
                <option value="MITIGATE">减轻</option>
                <option value="TRANSFER">转移</option>
                <option value="ACCEPT">接受</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                应对措施 <span className="text-red-400">*</span>
              </label>
              <textarea
                value={formData.response_plan}
                onChange={(e) =>
                  setFormData({ ...formData, response_plan: e.target.value })
                }
                placeholder="请详细描述应对措施"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={5}
              />
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>提交</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
