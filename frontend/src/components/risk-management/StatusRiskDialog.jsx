/**
 * 更新风险状态对话框
 */

import { useState } from "react";
import { Button, Dialog, DialogBody, DialogContent, DialogFooter, DialogHeader, DialogTitle, Input } from "../ui";



export default function StatusRiskDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    status: "",
    last_update: "",
    follow_up_date: "",
  });

  const handleSubmit = () => {
    if (!formData.status) {
      alert("请选择状态");
      return;
    }
    onSubmit(formData);
    setFormData({ status: "", last_update: "", follow_up_date: "" });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>更新风险状态</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                状态 <span className="text-red-400">*</span>
              </label>
              <select
                value={formData.status}
                onChange={(e) =>
                  setFormData({ ...formData, status: e.target.value })
                }
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">请选择</option>
                <option value="IDENTIFIED">已识别</option>
                <option value="ANALYZING">分析中</option>
                <option value="RESPONDING">应对中</option>
                <option value="MONITORING">监控中</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                最新进展
              </label>
              <textarea
                value={formData.last_update}
                onChange={(e) =>
                  setFormData({ ...formData, last_update: e.target.value })
                }
                placeholder="请输入最新进展"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={3}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                跟踪日期
              </label>
              <Input
                type="date"
                value={formData.follow_up_date}
                onChange={(e) =>
                  setFormData({ ...formData, follow_up_date: e.target.value })
                }
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
