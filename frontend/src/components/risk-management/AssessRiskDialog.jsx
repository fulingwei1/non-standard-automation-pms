/**
 * 风险评估对话框
 */

import { useState } from "react";
import { Button, Dialog, DialogBody, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "../ui";



export default function AssessRiskDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    probability: "",
    impact: "",
    risk_level: "",
  });

  const handleSubmit = () => {
    if (!formData.probability || !formData.impact) {
      alert("请选择发生概率和影响程度");
      return;
    }
    onSubmit(formData);
    setFormData({ probability: "", impact: "", risk_level: "" });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>风险评估</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                发生概率 <span className="text-red-400">*</span>
              </label>
              <select
                value={formData.probability}
                onChange={(e) =>
                  setFormData({ ...formData, probability: e.target.value })
                }
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">请选择</option>
                <option value="HIGH">高</option>
                <option value="MEDIUM">中</option>
                <option value="LOW">低</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                影响程度 <span className="text-red-400">*</span>
              </label>
              <select
                value={formData.impact}
                onChange={(e) =>
                  setFormData({ ...formData, impact: e.target.value })
                }
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">请选择</option>
                <option value="HIGH">高</option>
                <option value="MEDIUM">中</option>
                <option value="LOW">低</option>
              </select>
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
