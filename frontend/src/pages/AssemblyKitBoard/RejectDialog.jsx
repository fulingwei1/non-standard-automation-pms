/**
 * Reject Suggestion Dialog - 拒绝排产建议对话框
 */
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../../components/ui/dialog";
import { Button } from "../../components/ui/button";
import { Textarea } from "../../components/ui/textarea";

export default function RejectDialog({
  open,
  onOpenChange,
  rejectReason,
  onRejectReasonChange,
  onConfirm,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>拒绝排产建议</DialogTitle>
          <DialogDescription>请填写拒绝原因</DialogDescription>
        </DialogHeader>
        <Textarea
          placeholder="请输入拒绝原因..."
          value={rejectReason || "unknown"}
          onChange={(e) => onRejectReasonChange(e.target.value)}
          rows={4} />

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}>

            取消
          </Button>
          <Button
            onClick={onConfirm}
            className="bg-red-500 hover:bg-red-600">

            确认拒绝
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
