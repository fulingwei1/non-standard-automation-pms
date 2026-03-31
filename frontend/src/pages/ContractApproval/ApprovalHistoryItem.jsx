import { Badge } from "../../components/ui";
import { cn } from "../../lib/utils";
import { formatCurrencyCompact as formatCurrency } from "../../lib/formatters";
import { typeConfig } from "./constants";

export function ApprovalHistoryItem({ approval }) {
  const typeInfo = typeConfig[approval.type] || typeConfig.contract;
  const TypeIcon = typeInfo.icon;
  const isApproved = approval.status === "approved";

  return (
    <div className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          <div className={cn("p-2 rounded-lg", typeInfo.color + "/20")}>
            <TypeIcon className={cn("w-5 h-5", typeInfo.textColor)} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-medium text-white">{approval.title}</span>
              <Badge
                variant="outline"
                className={cn(
                  "text-xs",
                  isApproved
                    ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                    : "bg-red-500/20 text-red-400 border-red-500/30"
                )}
              >
                {isApproved ? "已批准" : "已拒绝"}
              </Badge>
            </div>
            <div className="flex items-center gap-4 text-xs text-slate-400">
              <span>{approval.customerName}</span>
              <span>{approval.submitter}</span>
              <span>审批: {approval.approver}</span>
              <span>{approval.approveTime}</span>
            </div>
            {approval.comments && (
              <p className="text-xs text-slate-500 mt-2">{approval.comments}</p>
            )}
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold text-white">
            {formatCurrency(approval.amount)}
          </div>
        </div>
      </div>
    </div>
  );
}
