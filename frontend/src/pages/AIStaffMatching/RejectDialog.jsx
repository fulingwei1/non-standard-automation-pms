// -*- coding: utf-8 -*-
import { Button } from "../../components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from "../../components/ui/dialog";

export default function RejectDialog({
  open,
  onOpenChange,
  selectedCandidate,
  rejectReason,
  setRejectReason,
  onConfirm
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>拒绝候选人</DialogTitle>
        </DialogHeader>
        <div className="py-4">
          <p className="text-sm text-slate-400 mb-4">
            请填写拒绝{" "}
            <span className="text-white font-medium">
              {selectedCandidate?.employee_name}
            </span>{" "}
            的原因：
          </p>
          <textarea
            value={rejectReason || "unknown"}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="请输入拒绝原因，如：工作负载过高、技能不匹配等"
            className="w-full h-24 px-3 py-2 rounded-md border border-white/10 bg-white/5 text-sm resize-none" />
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button
            variant="destructive"
            onClick={onConfirm}
            disabled={!rejectReason.trim()}>
            确认拒绝
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
