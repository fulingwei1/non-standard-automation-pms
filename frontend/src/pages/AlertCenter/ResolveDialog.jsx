/**
 * ResolveDialog - Dialog for resolving an alert
 */

import { Button } from "../../components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter } from
"../../components/ui/dialog";
import { getAlertLevelConfig } from "../../components/alert-center";

export default function ResolveDialog({
  open,
  onOpenChange,
  selectedAlert,
  resolveResult,
  setResolveResult,
  onResolve
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>解决预警</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          {selectedAlert &&
          <div className="text-sm text-slate-300">
              <p><strong>预警:</strong> {selectedAlert.title}</p>
              <p><strong>级别:</strong> {getAlertLevelConfig(selectedAlert.alert_level).label}</p>
          </div>
          }
          <div>
            <label className="text-sm font-medium text-slate-300">解决方案</label>
            <textarea
              value={resolveResult || "unknown"}
              onChange={(e) => setResolveResult(e.target.value)}
              className="w-full mt-1 p-2 bg-slate-800 border border-slate-700 rounded text-white"
              rows={3}
              placeholder="请输入解决方案..." />

          </div>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}>

            取消
          </Button>
          <Button
            onClick={() => onResolve(selectedAlert.id, resolveResult)}
            className="bg-emerald-500 hover:bg-emerald-600">

            确认解决
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
