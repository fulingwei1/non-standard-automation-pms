import { FileText } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Button,
} from "../../components/ui";
import { formatCurrency } from "../../lib/utils";

export function PaymentDetailDialog({
  payment,
  onClose,
  onApprove,
  onReject,
}) {
  return (
    <Dialog open={!!payment} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>付款详情</DialogTitle>
        </DialogHeader>

        {payment && (
          <div className="py-4 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400">单号</label>
                <p className="text-white font-medium">{payment.orderNo}</p>
              </div>
              <div>
                <label className="text-sm text-slate-400">类型</label>
                <p className="text-white font-medium">{payment.typeLabel}</p>
              </div>
              <div>
                <label className="text-sm text-slate-400">金额</label>
                <p className="text-amber-400 font-bold text-lg">
                  {formatCurrency(payment.amount)}
                </p>
              </div>
              <div>
                <label className="text-sm text-slate-400">申请人</label>
                <p className="text-white">{payment.submitter}</p>
              </div>
              {payment.projectName && (
                <div>
                  <label className="text-sm text-slate-400">项目</label>
                  <p className="text-white">{payment.projectName}</p>
                </div>
              )}
              {payment.supplier && (
                <div>
                  <label className="text-sm text-slate-400">供应商</label>
                  <p className="text-white">{payment.supplier}</p>
                </div>
              )}
              {payment.department && (
                <div>
                  <label className="text-sm text-slate-400">部门</label>
                  <p className="text-white">{payment.department}</p>
                </div>
              )}
              <div>
                <label className="text-sm text-slate-400">提交时间</label>
                <p className="text-white">{payment.submitTime}</p>
              </div>
            </div>

            {payment.description && (
              <div>
                <label className="text-sm text-slate-400">描述</label>
                <p className="text-white">{payment.description}</p>
              </div>
            )}

            {payment.attachments?.length > 0 && (
              <div>
                <label className="text-sm text-slate-400">附件</label>
                <div className="space-y-2 mt-2">
                  {payment.attachments.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-2 p-2 bg-slate-800/40 rounded"
                    >
                      <FileText className="w-4 h-4 text-slate-400" />
                      <span className="text-sm text-white">{file}</span>
                      <Button variant="ghost" size="sm" className="ml-auto">
                        下载
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            关闭
          </Button>
          <Button
            className="bg-emerald-500 hover:bg-emerald-600"
            onClick={() => onApprove(payment)}
          >
            审批通过
          </Button>
          <Button
            variant="outline"
            className="text-red-400 border-red-500/30 hover:bg-red-500/20"
            onClick={() => onReject(payment)}
          >
            拒绝
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
