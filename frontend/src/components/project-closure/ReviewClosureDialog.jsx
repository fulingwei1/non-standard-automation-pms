/**
 * 结项评审对话框
 */

import { useState } from "react";
import { Button, Dialog, DialogBody, DialogContent, DialogFooter, DialogHeader, DialogTitle, Input } from "../ui";



export default function ReviewClosureDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    review_result: "",
    review_notes: ""
  });

  const handleSubmit = () => {
    if (!formData.review_result.trim()) {
      alert("请填写评审结果");
      return;
    }
    onSubmit(formData);
    setFormData({ review_result: "", review_notes: "" });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>结项评审</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                评审结果 <span className="text-red-400">*</span>
              </label>
              <Input
                value={formData.review_result}
                onChange={(e) =>
                  setFormData({ ...formData, review_result: e.target.value })
                }
                placeholder="请输入评审结果"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                评审记录
              </label>
              <textarea
                value={formData.review_notes}
                onChange={(e) =>
                  setFormData({ ...formData, review_notes: e.target.value })
                }
                placeholder="请输入评审记录"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={4}
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
