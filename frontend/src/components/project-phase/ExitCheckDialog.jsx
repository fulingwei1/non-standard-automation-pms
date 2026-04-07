/**
 * 阶段出口检查对话框
 */

import { useState } from "react";



export default function ExitCheckDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    check_result: "",
    notes: ""
  });

  const handleSubmit = () => {
    if (!formData.check_result.trim()) {
      alert("请填写检查结果");
      return;
    }
    onSubmit(formData);
    setFormData({ check_result: "", notes: "" });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>阶段出口检查</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                检查结果 <span className="text-red-400">*</span>
              </label>
              <textarea
                value={formData.check_result}
                onChange={(e) =>
                  setFormData({ ...formData, check_result: e.target.value })
                }
                placeholder="请输入检查结果"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={4}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                检查说明
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) =>
                  setFormData({ ...formData, notes: e.target.value })
                }
                placeholder="请输入检查说明（可选）"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={3}
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
