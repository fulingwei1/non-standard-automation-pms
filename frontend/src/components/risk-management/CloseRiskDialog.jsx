/**
 * 关闭风险对话框
 */

import { useState } from "react";



export default function CloseRiskDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    closed_reason: "",
  });

  const handleSubmit = () => {
    if (!formData.closed_reason.trim()) {
      alert("请填写关闭原因");
      return;
    }
    onSubmit(formData);
    setFormData({ closed_reason: "" });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>关闭风险</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              关闭原因 <span className="text-red-400">*</span>
            </label>
            <textarea
              value={formData.closed_reason}
              onChange={(e) =>
                setFormData({ ...formData, closed_reason: e.target.value })
              }
              placeholder="请说明风险关闭的原因"
              className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
              rows={4}
            />
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>关闭</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
