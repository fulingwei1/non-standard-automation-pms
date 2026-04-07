/**
 * 更新 KPI 值弹窗
 */
import { useState, useEffect } from "react";



export default function UpdateValueDialog({ kpi, open, onClose, onSubmit, loading }) {
  const [value, setValue] = useState(kpi?.current_value || 0);

  useEffect(() => {
    if (kpi) {
      setValue(kpi.current_value || 0);
    }
  }, [kpi]);

  const handleSubmit = () => {
    onSubmit({ current_value: parseFloat(value) });
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>更新 KPI 值</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-slate-400 mb-1">KPI 名称</p>
              <p className="text-base font-medium text-white">{kpi?.name}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                当前值 ({kpi?.unit || "%"}) *
              </label>
              <Input
                type="number"
                step="0.01"
                value={value || "unknown"}
                onChange={(e) => setValue(e.target.value)}
                className="bg-slate-800/50 border-slate-700 text-lg"
              />
            </div>

            <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700">
              <p className="text-sm text-slate-400">目标值</p>
              <p className="text-lg font-semibold text-white">
                {kpi?.target_value} {kpi?.unit || "%"}
              </p>
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? "更新中..." : "确认更新"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
