import {
  FileText,
} from "lucide-react";


import { cn, formatCurrency } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { typeConfig } from "./constants";

function PaymentRow({ payment, onView, onApprove, onReject }) {
  const typeConf = typeConfig[payment.type];
  const TypeIcon = typeConf?.icon || FileText;

  return (
    <div className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Badge
              variant="outline"
              className={cn("text-xs", typeConf?.color)}
            >
              <TypeIcon className="w-3 h-3 mr-1" />
              {payment.typeLabel}
            </Badge>

            {(payment.priority === "high" || payment.priority === "urgent") && (
              <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                {payment.priority === "urgent" ? "紧急" : "高优先级"}
              </Badge>
            )}

            <span className="text-sm text-slate-400">
              {payment.daysPending > 0
                ? `待审批${payment.daysPending}天`
                : "今日提交"}
            </span>
          </div>

          <div className="font-medium text-white text-sm mb-1">
            {payment.orderNo}
          </div>

          <div className="text-xs text-slate-400 space-y-1">
            {payment.projectName && <div>项目: {payment.projectName}</div>}
            {payment.supplier && <div>供应商: {payment.supplier}</div>}
            {payment.department && <div>部门: {payment.department}</div>}
            <div>
              申请人: {payment.submitter} · {payment.submitTime.split(" ")[1]}
            </div>
            {payment.description && (
              <div className="text-slate-500 mt-1">{payment.description}</div>
            )}
          </div>

          {payment.attachments?.length > 0 && (
            <div className="flex items-center gap-2 mt-2">
              <FileText className="w-3 h-3 text-slate-500" />
              <span className="text-xs text-slate-500">
                {payment.attachments.length}个附件
              </span>
            </div>
          )}
        </div>

        <div className="text-right ml-4">
          <div className="text-lg font-bold text-amber-400 mb-2">
            {formatCurrency(payment.amount)}
          </div>
          {payment.dueDate && (
            <div className="text-xs text-slate-400 mb-3">
              到期: {payment.dueDate}
            </div>
          )}
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="text-xs"
              onClick={() => onView(payment)}
            >
              <Eye className="w-3 h-3 mr-1" />
              查看
            </Button>
            <Button
              size="sm"
              className="text-xs bg-emerald-500/20 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/30"
              onClick={() => onApprove(payment)}
            >
              <Check className="w-3 h-3 mr-1" />
              通过
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="text-xs text-red-400 border-red-500/30 hover:bg-red-500/20"
              onClick={() => onReject(payment)}
            >
              <X className="w-3 h-3 mr-1" />
              拒绝
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function PaymentList({
  filteredPayments,
  onView,
  onApprove,
  onReject,
}) {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <ClipboardCheck className="h-5 w-5 text-amber-400" />
              待审批付款
            </CardTitle>
            <Badge
              variant="outline"
              className="bg-amber-500/20 text-amber-400 border-amber-500/30"
            >
              {filteredPayments.length}笔
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {filteredPayments.map((payment) => (
              <PaymentRow
                key={payment.id}
                payment={payment}
                onView={onView}
                onApprove={onApprove}
                onReject={onReject}
              />
            ))}
            {filteredPayments.length === 0 && (
              <div className="text-center py-12 text-slate-500">
                暂无待审批付款
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
