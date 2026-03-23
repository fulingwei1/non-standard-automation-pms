/**
 * 推进阶段对话框
 */

import { useState } from "react";



export default function AdvanceDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    actual_start_date: "",
    notes: ""
  });

  const handleSubmit = () => {
    onSubmit(formData);
    setFormData({ actual_start_date: "", notes: "" });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>推进阶段</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                实际开始日期
              </label>
              <Input
                type="date"
                value={formData.actual_start_date}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    actual_start_date: e.target.value
                  })
                }
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                推进说明
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) =>
                  setFormData({ ...formData, notes: e.target.value })
                }
                placeholder="请输入推进说明（可选）"
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
