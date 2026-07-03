import { Eye } from "lucide-react";
import {
  Card,
  CardContent,
  Badge,
  Button,
} from "../../components/ui";
import { cn, formatCurrency } from "../../lib/utils";
import {
  TYPE_ICON_MAP,
  DEFAULT_TYPE_ICON,
  TYPE_LABEL_MAP,
  DEFAULT_TYPE_LABEL,
  TYPE_BADGE_CLASS_MAP,
} from "./constants";

/**
 * Reusable card for displaying a single approval item.
 *
 * Props:
 *   approval      — approval data object
 *   showActions   — show Approve / Reject buttons (pending tab)
 *   onApprove     — (id) => void
 *   onReject      — (id) => void
 *   statusBadge   — optional override badge element rendered next to type badge
 *   cardKey       — React key (forwarded via parent map)
 */
export function ApprovalCard({
  approval,
  showActions = false,
  onApprove,
  onReject,
  statusBadge,
}) {
  const TypeIcon = TYPE_ICON_MAP[approval.type] || DEFAULT_TYPE_ICON;
  const typeLabel = TYPE_LABEL_MAP[approval.type] || DEFAULT_TYPE_LABEL;
  const typeBadgeClass = TYPE_BADGE_CLASS_MAP[approval.type] || "";

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            {/* Title row */}
            <div className="flex items-center gap-3 mb-2">
              <TypeIcon className="h-5 w-5 text-slate-400" />
              <h3 className="text-lg font-semibold text-white">
                {approval.title}
              </h3>
              <Badge
                variant="outline"
                className={cn(typeBadgeClass)}>
                {typeLabel}
              </Badge>
              {approval.priority === "high" && (
                <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                  紧急
                </Badge>
              )}
              {statusBadge}
            </div>

            {/* Applicant / department */}
            <div className="text-sm text-slate-400 mb-2">
              {approval.department} · {approval.applicant}
            </div>

            {/* Details */}
            <div className="text-sm text-slate-500 mb-3">
              {approval.items && `物品: ${approval.items.join("、")}`}
              {approval.purpose &&
                `用途: ${approval.purpose} · 目的地: ${approval.destination || "待定"}`}
              {approval.item && `资产: ${approval.item}`}
              {approval.room &&
                `会议室: ${approval.room} · 时间: ${approval.date} ${approval.time}`}
              {approval.leaveType &&
                `类型: ${approval.leaveType} · 天数: ${approval.days} 天 · 日期: ${approval.date}`}
            </div>

            {/* Reject reason (when present) */}
            {approval.rejectReason && (
              <div className="text-sm text-red-400/80 mb-3 p-2 bg-red-500/10 rounded">
                拒绝原因: {approval.rejectReason}
              </div>
            )}

            {/* Footer row */}
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-4 text-slate-500">
                <span>提交: {approval.submitTime}</span>
                {approval.approvedTime && (
                  <span className="text-green-400">
                    批准: {approval.approvedTime}
                  </span>
                )}
                {approval.rejectedTime && (
                  <span className="text-red-400">
                    拒绝: {approval.rejectedTime}
                  </span>
                )}
                {approval.approver && (
                  <span>审批人: {approval.approver}</span>
                )}
              </div>
              {approval.amount && (
                <span className="font-medium text-amber-400">
                  {formatCurrency(approval.amount)}
                </span>
              )}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex gap-2 ml-4">
            <Button variant="outline" size="sm">
              <Eye className="w-4 h-4" />
            </Button>
            {showActions && (
              <>
                <Button size="sm" onClick={() => onApprove(approval.id)}>
                  批准
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onReject(approval.id)}>
                  拒绝
                </Button>
              </>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
