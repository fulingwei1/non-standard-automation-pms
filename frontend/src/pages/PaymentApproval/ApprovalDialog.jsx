import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Button,
} from "../../components/ui";
import { formatCurrency } from "../../lib/utils";

export function ApprovalDialog({
  open,
  onOpenChange,
  approvalAction,
  approvalComment,
  onCommentChange,
  selectedPayment,
  onConfirm,
}) {
  const isApprove = approvalAction === "approve";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isApprove ? "审批通过" : "审批拒绝"}</DialogTitle>
          <DialogDescription>
            {selectedPayment && (
              <div className="mt-2">
                <p className="text-sm text-slate-400">
                  单号: {selectedPayment.orderNo}
                </p>
                <p className="text-sm text-slate-400">
                  金额: {formatCurrency(selectedPayment.amount)}
                </p>
              </div>
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="py-4 space-y-4">
          <div className="space-y-2">
            <label className="text-sm text-slate-400">
              {isApprove ? "审批意见" : "拒绝原因"}
              {!isApprove && <span className="text-red-400"> *</span>}
            </label>
            <textarea
              value={approvalComment}
              onChange={(e) => onCommentChange(e.target.value)}
              placeholder={
                isApprove
                  ? "请输入审批意见（可选）"
                  : "请输入拒绝原因（必填）"
              }
              className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white resize-none h-24"
              required={!isApprove}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button
            className={
              isApprove
                ? "bg-emerald-500 hover:bg-emerald-600"
                : "bg-red-500 hover:bg-red-600"
            }
            onClick={onConfirm}
          >
            {isApprove ? "确认通过" : "确认拒绝"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
