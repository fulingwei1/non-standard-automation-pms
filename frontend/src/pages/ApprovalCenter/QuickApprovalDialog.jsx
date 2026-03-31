import { Loader2 } from "lucide-react";
import { Button } from "../../components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../../components/ui/dialog";
import { Textarea } from "../../components/ui/textarea";

const QuickApprovalDialog = ({
  dialogState,
  setDialogState,
  onClose,
  onSubmit,
}) => (
  <Dialog
    open={dialogState.open}
    onOpenChange={(open) => !open && onClose()}
  >
    <DialogContent className="bg-slate-800 border-slate-700">
      <DialogHeader>
        <DialogTitle className="text-white">
          {dialogState.action === "approve" ? "审批通过" : "审批驳回"}
        </DialogTitle>
      </DialogHeader>

      <div className="space-y-4">
        <div>
          <p className="text-sm text-slate-400 mb-2">审批标题</p>
          <p className="text-white">
            {dialogState.item?.instance_title || dialogState.item?.instance?.title}
          </p>
        </div>

        <div>
          <p className="text-sm text-slate-400 mb-2">审批意见</p>
          <Textarea
            placeholder={dialogState.action === "approve" ? "同意" : "请输入驳回理由"}
            value={dialogState.comment}
            onChange={(e) =>
              setDialogState((prev) => ({
                ...prev,
                comment: e.target.value,
              }))
            }
            className="bg-slate-900/50 border-slate-700"
          />
        </div>
      </div>

      <DialogFooter>
        <Button
          variant="outline"
          className="border-slate-600"
          onClick={onClose}
          disabled={dialogState.submitting}
        >
          取消
        </Button>
        <Button
          className={
            dialogState.action === "approve"
              ? "bg-emerald-600 hover:bg-emerald-700"
              : "bg-red-600 hover:bg-red-700"
          }
          onClick={onSubmit}
          disabled={dialogState.submitting}
        >
          {dialogState.submitting && (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          )}
          确认{dialogState.action === "approve" ? "通过" : "驳回"}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
);

export default QuickApprovalDialog;
