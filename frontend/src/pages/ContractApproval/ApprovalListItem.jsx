import { cn } from "../../lib/utils";
import { formatCurrencyCompact as formatCurrency } from "../../lib/formatters";
import { typeConfig, priorityConfig } from "./constants";

export function ApprovalListItem({ approval, onViewDetail }) {
  const typeInfo = typeConfig[approval.type] || typeConfig.contract;
  const priorityInfo = priorityConfig[approval.priority] || priorityConfig.medium;
  const TypeIcon = typeInfo.icon;

  return (
    <div className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start gap-3 flex-1">
          <div className={cn("p-2 rounded-lg", typeInfo.color + "/20")}>
            <TypeIcon className={cn("w-5 h-5", typeInfo.textColor)} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-medium text-white">{approval.title}</span>
              <Badge variant="outline" className={cn("text-xs", typeInfo.textColor)}>
                {typeInfo.label}
              </Badge>
              <Badge variant="outline" className={cn("text-xs", priorityInfo.textColor)}>
                {priorityInfo.label}
              </Badge>
            </div>
            <div className="flex items-center gap-4 text-xs text-slate-400">
              <span className="flex items-center gap-1">
                <Building2 className="w-3 h-3" />
                {approval.customerShort}
              </span>
              <span className="flex items-center gap-1">
                <User className="w-3 h-3" />
                {approval.submitter}
              </span>
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {approval.submitTime}
              </span>
            </div>
          </div>
        </div>
        <div className="text-right mr-4">
          <div className="text-lg font-bold text-white">
            {formatCurrency(approval.totalAmount)}
          </div>
          {approval.originalAmount && (
            <div className="text-xs text-slate-400 line-through">
              {formatCurrency(approval.originalAmount)}
            </div>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onViewDetail(approval)}
          className="flex items-center gap-2"
        >
          <Eye className="w-4 h-4" />
          查看详情
        </Button>
        <Button
          size="sm"
          onClick={() => onViewDetail(approval)}
          className="flex items-center gap-2"
        >
          <CheckCircle2 className="w-4 h-4" />
          审批
        </Button>
      </div>
    </div>
  );
}
