import { motion } from "framer-motion";
import {
    Package,
    Eye,
    Edit3,
    Trash2,
    CheckCircle2,
    AlertTriangle,
} from "lucide-react";
import { Button } from "../../../components/ui/button";
import { Badge } from "../../../components/ui/badge";
import { cn } from "../../../lib/utils";
import {
    ORDER_STATUS,
    ORDER_STATUS_CONFIGS,
    ORDER_URGENCY_CONFIGS,
    PurchaseOrderUtils
} from "../../../components/purchase-orders";
import { DynamicIcon } from "../../../utils/iconMap.jsx";

export function OrderCard({ order, onView, onEdit, onDelete, onSubmit, onApprove }) {
    const status = ORDER_STATUS_CONFIGS[order.status];
    const urgency = ORDER_URGENCY_CONFIGS[order.urgency];

    return (
        <motion.div
            whileHover={{ scale: 1.01 }}
            className="bg-surface-1 rounded-xl border border-border p-4 hover:border-border/80 transition-colors"
        >
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <span className="font-mono font-semibold text-white">{order.id}</span>
                        {order.urgency !== "normal" && (
                            <Badge variant="outline" className={cn("text-[10px] border", urgency?.color)}>
                                {urgency?.label}
                            </Badge>
                        )}
                    </div>
                    <p className="text-sm text-slate-400">{order.supplierName}</p>
                </div>
                <Badge className={cn("gap-1", status?.color)}>
                    {status?.icon && <DynamicIcon name={status.icon} className="w-3 h-3" />}
                    {status?.label}
                </Badge>
            </div>

            {/* Project Info */}
            <div className="flex items-center gap-2 mb-3 text-sm">
                <span className="text-accent">{order.projectId}</span>
                <span className="text-slate-500">·</span>
                <span className="text-slate-400 truncate">{order.projectName}</span>
            </div>

            {/* Progress */}
            <div className="mb-3">
                <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-slate-400">到货进度</span>
                    <span className="text-white">
                        {order.receivedCount}/{order.itemCount} 项
                    </span>
                </div>
                <div className="h-1.5 bg-surface-2 rounded-full overflow-hidden">
                    <div
                        className={cn(
                            "h-full rounded-full transition-all",
                            order.status === "completed"
                                ? "bg-emerald-500"
                                : order.status === "delayed"
                                    ? "bg-red-500"
                                    : "bg-accent"
                        )}
                        style={{ width: `${(order.receivedCount / order.itemCount) * 100}%` }}
                    />
                </div>
            </div>

            {/* Info Grid */}
            <div className="grid grid-cols-2 gap-3 mb-3 text-sm">
                <div>
                    <span className="text-slate-500 text-xs">订单金额</span>
                    <p className="text-white font-medium">
                        ¥{(order.totalAmount || 0).toLocaleString()}
                    </p>
                </div>
                <div>
                    <span className="text-slate-500 text-xs">预计到货</span>
                    <p className={cn("font-medium", order.status === "delayed" ? "text-red-400" : "text-white")}>
                        {order.delayedDate || PurchaseOrderUtils.formatDate(order.expected_date)}
                    </p>
                </div>
            </div>

            {/* Delay Reason */}
            {order.delayReason && (
                <div className="mb-3 p-2 rounded-lg bg-red-500/10 text-xs text-red-300 flex items-center gap-2">
                    <AlertTriangle className="w-3 h-3" />
                    {order.delayReason}
                </div>
            )}

            {/* Actions */}
            <div className="flex items-center justify-between pt-3 border-t border-border/50">
                <span className="text-xs text-slate-500">采购员：{order.buyer}</span>
                <div className="flex gap-1">
                    <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => onView(order)} title="查看详情">
                        <Eye className="w-3.5 h-3.5" />
                    </Button>
                    {order.status === ORDER_STATUS.DRAFT && onEdit && (
                        <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => onEdit(order)} title="编辑">
                            <Edit3 className="w-3.5 h-3.5" />
                        </Button>
                    )}
                    {order.status === ORDER_STATUS.DRAFT && onDelete && (
                        <Button variant="ghost" size="sm" className="h-7 px-2 text-red-400 hover:text-red-300" onClick={() => onDelete(order)} title="删除">
                            <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                    )}
                    {(order.status === ORDER_STATUS.PENDING || order.status === ORDER_STATUS.PARTIAL_RECEIVED) && onSubmit && (
                        <Button variant="ghost" size="sm" className="h-7 px-2 text-blue-400 hover:text-blue-300" onClick={() => onSubmit(order)} title="确认收货">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                        </Button>
                    )}
                    {order.status === ORDER_STATUS.DRAFT && onApprove && (
                        <Button variant="ghost" size="sm" className="h-7 px-2 text-emerald-400 hover:text-emerald-300" onClick={() => onApprove(order)} title="提交审批">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                        </Button>
                    )}
                </div>
            </div>
        </motion.div>
    );
}
