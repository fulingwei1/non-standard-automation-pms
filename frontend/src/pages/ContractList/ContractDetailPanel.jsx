import { motion } from "framer-motion";
import {
  X,
  Building2,
  Calendar,
  Clock,
  Shield,
  User,
  FileText,
  Paperclip,
  Download,
  Edit,
  CheckCircle2,
  AlertTriangle,
  XCircle,
} from "lucide-react";
import { Button, Badge, Progress } from "../../components/ui";
import { cn } from "../../lib/utils";
import { statusConfig, paymentTypeLabels } from "./constants";

function PaymentTermItem({ term }) {
  const isPaid = term.status === "paid";
  const isOverdue =
    term.status === "overdue" ||
    (term.status === "pending" &&
      term.dueDate &&
      new Date(term.dueDate) < new Date());

  return (
    <div
      className={cn(
        "p-3 rounded-lg border",
        isPaid
          ? "bg-emerald-500/10 border-emerald-500/20"
          : isOverdue
          ? "bg-red-500/10 border-red-500/20"
          : "bg-surface-50 border-white/5"
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isPaid ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          ) : isOverdue ? (
            <AlertTriangle className="w-4 h-4 text-red-400" />
          ) : (
            <Clock className="w-4 h-4 text-slate-400" />
          )}
          <span className="text-sm text-white">
            {paymentTypeLabels[term.type]} ({term.percent}%)
          </span>
        </div>
        <span
          className={cn(
            "text-sm font-medium",
            isPaid
              ? "text-emerald-400"
              : isOverdue
              ? "text-red-400"
              : "text-amber-400"
          )}
        >
          ¥{(term.amount / 10000).toFixed(1)}万
        </span>
      </div>
      <div className="text-xs text-slate-400 mt-1">
        {isPaid ? (
          <span className="text-emerald-400">已收款: {term.paidDate}</span>
        ) : (
          <span className={isOverdue ? "text-red-400" : ""}>
            应收日期: {term.dueDate || "-"}
            {isOverdue && " (已逾期)"}
          </span>
        )}
      </div>
    </div>
  );
}

export default function ContractDetailPanel({ contract, onClose }) {
  const statusConf = statusConfig[contract.status] || statusConfig.draft;
  const paymentProgress =
    contract.totalAmount > 0
      ? (contract.paidAmount / contract.totalAmount) * 100
      : 0;

  return (
    <motion.div
      initial={{ x: "100%" }}
      animate={{ x: 0 }}
      exit={{ x: "100%" }}
      transition={{ type: "spring", damping: 25, stiffness: 200 }}
      className="fixed right-0 top-0 h-full w-full md:w-[500px] bg-surface-100/95 backdrop-blur-xl border-l border-white/5 shadow-2xl z-50 flex flex-col"
    >
      {/* Header */}
      <div className="p-4 border-b border-white/5">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-lg font-semibold text-white">
                {contract.name}
              </h2>
            </div>
            <p className="text-sm text-slate-400">{contract.id}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>
        <div className="flex items-center gap-2 mt-3">
          <Badge
            className={cn(
              "text-xs",
              statusConf.textColor,
              "bg-transparent border-0"
            )}
          >
            <div
              className={cn("w-2 h-2 rounded-full mr-1", statusConf.color)}
            />
            {statusConf.label}
          </Badge>
        </div>
      </div>

      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Amount summary */}
        <div className="p-4 bg-gradient-to-br from-amber-500/10 to-orange-500/5 border border-amber-500/20 rounded-xl">
          <div className="flex items-center justify-between mb-3">
            <div>
              <div className="text-sm text-slate-400">合同金额</div>
              <div className="text-2xl font-bold text-amber-400">
                ¥{(contract.totalAmount / 10000).toFixed(2)}万
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-slate-400">回款进度</div>
              <div className="text-lg font-semibold text-emerald-400">
                {paymentProgress.toFixed(0)}%
              </div>
            </div>
          </div>
          <Progress value={paymentProgress} className="h-2" />
          <div className="flex justify-between text-xs text-slate-400 mt-2">
            <span>已收: ¥{(contract.paidAmount / 10000).toFixed(1)}万</span>
            <span>
              待收: ¥
              {((contract.totalAmount - contract.paidAmount) / 10000).toFixed(
                1
              )}
              万
            </span>
          </div>
        </div>

        {/* Basic info */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">基本信息</h3>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-3">
              <Building2 className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">客户:</span>
              <span className="text-white">{contract.customerShort}</span>
            </div>
            {contract.projectName && (
              <div className="flex items-center gap-3">
                <FileText className="w-4 h-4 text-slate-500" />
                <span className="text-slate-400">项目:</span>
                <span className="text-blue-400">{contract.projectName}</span>
              </div>
            )}
            <div className="flex items-center gap-3">
              <Calendar className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">签约日期:</span>
              <span className="text-white">{contract.signDate || "-"}</span>
            </div>
            <div className="flex items-center gap-3">
              <Clock className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">交付日期:</span>
              <span className="text-white">{contract.deliveryDate || "-"}</span>
            </div>
            <div className="flex items-center gap-3">
              <Shield className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">质保期:</span>
              <span className="text-white">
                {contract.warrantyMonths}个月 (至{" "}
                {contract.warrantyEndDate || "-"})
              </span>
            </div>
            <div className="flex items-center gap-3">
              <User className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">销售:</span>
              <span className="text-white">{contract.salesPerson}</span>
            </div>
          </div>
        </div>

        {/* Payment terms */}
        {contract.paymentTerms?.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-slate-400">付款条款</h3>
            <div className="space-y-2">
              {(contract.paymentTerms || []).map((term, index) => (
                <PaymentTermItem key={index} term={term} />
              ))}
            </div>
          </div>
        )}

        {/* Attachments */}
        {contract.attachments?.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-slate-400">合同附件</h3>
            <div className="space-y-2">
              {(contract.attachments || []).map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-surface-50 rounded-lg"
                >
                  <div className="flex items-center gap-2">
                    <Paperclip className="w-4 h-4 text-slate-400" />
                    <span className="text-sm text-white">{file}</span>
                  </div>
                  <Button variant="ghost" size="sm">
                    <Download className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Notes */}
        {contract.notes && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-slate-400">备注</h3>
            <p className="text-sm text-white bg-surface-50 p-3 rounded-lg">
              {contract.notes}
            </p>
          </div>
        )}

        {/* Termination reason */}
        {contract.terminateReason && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <div className="flex items-center gap-2 text-red-400 text-sm">
              <XCircle className="w-4 h-4" />
              终止原因: {contract.terminateReason}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/5 flex gap-2">
        <Button variant="outline" className="flex-1" onClick={onClose}>
          关闭
        </Button>
        {contract.status === "active" && (
          <Button className="flex-1">
            <Edit className="w-4 h-4 mr-2" />
            编辑
          </Button>
        )}
      </div>
    </motion.div>
  );
}
