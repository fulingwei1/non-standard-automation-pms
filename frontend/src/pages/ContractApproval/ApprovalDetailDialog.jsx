import { CheckCircle2, XCircle, Loader2, FileText, Download } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Badge,
  Button,
  Textarea,
} from "../../components/ui";
import { cn } from "../../lib/utils";
import { formatCurrencyCompact as formatCurrency } from "../../lib/formatters";
import { typeConfig, priorityConfig } from "./constants";

const PAYMENT_TERM_LABELS = {
  deposit: "签约款",
  progress: "进度款",
  acceptance: "验收款",
};

function getPaymentTermLabel(type) {
  return PAYMENT_TERM_LABELS[type] || "质保金";
}

export function ApprovalDetailDialog({
  open,
  onOpenChange,
  approval,
  approvalComments,
  setApprovalComments,
  actionLoading,
  actionError,
  onApprove,
  onReject,
}) {
  if (!approval) return null;

  const typeInfo = typeConfig[approval.type] || typeConfig.contract;
  const priorityInfo = priorityConfig[approval.priority] || priorityConfig.medium;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>审批详情</DialogTitle>
          <DialogDescription>查看详细信息并做出审批决定</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Action error banner */}
          {actionError && (
            <div className="p-3 rounded border border-red-500/30 bg-red-500/10 text-sm text-red-200">
              {actionError}
            </div>
          )}

          {/* Basic info grid */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-slate-400">类型</p>
              <p className="text-white font-medium">{typeInfo.label}</p>
            </div>
            <div>
              <p className="text-sm text-slate-400">优先级</p>
              <Badge
                variant="outline"
                className={cn("text-xs", priorityInfo.textColor)}
              >
                {priorityInfo.label}
              </Badge>
            </div>
            <div>
              <p className="text-sm text-slate-400">客户</p>
              <p className="text-white font-medium">{approval.customerName}</p>
            </div>
            <div>
              <p className="text-sm text-slate-400">项目</p>
              <p className="text-white font-medium">{approval.projectName}</p>
            </div>
            <div>
              <p className="text-sm text-slate-400">提交人</p>
              <p className="text-white font-medium">{approval.submitter}</p>
            </div>
            <div>
              <p className="text-sm text-slate-400">提交时间</p>
              <p className="text-white font-medium">{approval.submitTime}</p>
            </div>
            <div className="col-span-2">
              <p className="text-sm text-slate-400">金额</p>
              <p className="text-2xl font-bold text-white">
                {formatCurrency(approval.totalAmount)}
              </p>
              {approval.originalAmount && (
                <p className="text-sm text-slate-400 line-through">
                  原价: {formatCurrency(approval.originalAmount)}
                </p>
              )}
            </div>
          </div>

          {/* Description */}
          {approval.description && (
            <div>
              <p className="text-sm text-slate-400 mb-2">描述</p>
              <p className="text-white">{approval.description}</p>
            </div>
          )}

          {/* Payment terms */}
          {approval.paymentTerms && (
            <div>
              <p className="text-sm text-slate-400 mb-2">付款条款</p>
              <div className="space-y-2">
                {(approval.paymentTerms || []).map((term, index) => (
                  <div
                    key={index}
                    className="p-2 bg-slate-800/40 rounded border border-slate-700/50"
                  >
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-white">
                        {getPaymentTermLabel(term.type)} - {term.percent}%
                      </span>
                      <span className="text-white font-medium">
                        {formatCurrency(term.amount)}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">
                      到期日: {term.dueDate}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Attachments */}
          {approval.attachments?.length > 0 && (
            <div>
              <p className="text-sm text-slate-400 mb-2">附件</p>
              <div className="flex flex-wrap gap-2">
                {(approval.attachments || []).map((file, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    className="flex items-center gap-2"
                  >
                    <FileText className="w-4 h-4" />
                    {file}
                    <Download className="w-3 h-3" />
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Notes */}
          {approval.notes && (
            <div>
              <p className="text-sm text-slate-400 mb-2">备注</p>
              <p className="text-white">{approval.notes}</p>
            </div>
          )}

          {/* Approval comments */}
          <div>
            <p className="text-sm text-slate-400 mb-2">审批意见</p>
            <Textarea
              placeholder="请输入审批意见..."
              value={approvalComments}
              onChange={(e) => setApprovalComments(e.target.value)}
              rows={4}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button
            variant="destructive"
            onClick={onReject}
            disabled={actionLoading}
            className="flex items-center gap-2"
          >
            {actionLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <XCircle className="w-4 h-4" />
            )}
            {actionLoading ? "处理中..." : "拒绝"}
          </Button>
          <Button
            onClick={onApprove}
            disabled={actionLoading}
            className="flex items-center gap-2"
          >
            {actionLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <CheckCircle2 className="w-4 h-4" />
            )}
            {actionLoading ? "处理中..." : "批准"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
