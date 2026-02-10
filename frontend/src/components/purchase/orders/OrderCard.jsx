/**
 * OrderCard - 采购订单卡片组件
 * 显示单个采购订单的关键信息和操作按钮
 */

import { motion } from "framer-motion";
import {
  Package,
  Eye,
  Edit3,
  Trash2,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { Card, Badge, Button } from "../../../ui";
import { cn } from "../../../../lib/utils";
import {
  ORDER_STATUS,
  ORDER_URGENCY,
  formatOrderAmount,
  formatOrderDate,
  calculateProgress,
  getProgressColor,
  canEditOrder,
  canDeleteOrder,
} from "./purchaseOrderConstants";

export default function OrderCard({
  order,
  onView,
  onEdit,
  onDelete,
  onSubmit,
  onApprove,
}) {
  const statusKey = (order.status || "").toString().toLowerCase();
  const urgencyKey = (order.urgency || "").toString().toLowerCase();
  const status = ORDER_STATUS[statusKey] || ORDER_STATUS.draft;
  const urgency = ORDER_URGENCY[urgencyKey] || ORDER_URGENCY.normal;
  const StatusIcon = status.icon;
  const expectedDate = order.expected_date || order.expectedDate;

  // 计算进度
  const progress = calculateProgress(order.receivedCount, order.itemCount);
  const progressColor = getProgressColor(statusKey, progress);

  // 判断是否延期
  const isOrderDelayed = statusKey === "delayed" ||
    (expectedDate && new Date(expectedDate) < new Date() &&
     !["completed", "cancelled"].includes(statusKey));

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-4 hover:border-slate-600/80 transition-colors"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono font-semibold text-white">
              {order.id}
            </span>
            {order.urgency !== "normal" && (
              <Badge
                variant="outline"
                className={cn("text-[10px] border", urgency.borderColor, urgency.textColor)}
              >
                {urgency.label}
              </Badge>
            )}
          </div>
          <p className="text-sm text-slate-400">{order.supplierName}</p>
        </div>
        <Badge className={cn("gap-1", status.color, "text-white")}>
          <StatusIcon className="w-3 h-3" />
          {status.label}
        </Badge>
      </div>

      {/* Project Info */}
      <div className="flex items-center gap-2 mb-3 text-sm">
        <span className="text-blue-400">{order.projectId}</span>
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
        <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
          <div
            className={cn("h-full rounded-full transition-all", progressColor)}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-2 gap-3 mb-3 text-sm">
        <div>
          <span className="text-slate-500 text-xs">订单金额</span>
          <p className="text-white font-medium">
            {formatOrderAmount(order.totalAmount)}
          </p>
        </div>
        <div>
          <span className="text-slate-500 text-xs">预计到货</span>
          <p
            className={cn(
              "font-medium",
              isOrderDelayed ? "text-red-400" : "text-white",
            )}
          >
            {order.delayedDate || formatOrderDate(expectedDate)}
          </p>
        </div>
      </div>

      {/* Delay Reason */}
      {order.delayReason && (
        <div className="mb-3 p-2 rounded-lg bg-red-500/10 text-xs text-red-300 flex items-center gap-2">
          <AlertTriangle className="w-3 h-3 flex-shrink-0" />
          <span className="line-clamp-2">{order.delayReason}</span>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-slate-700/50">
        <span className="text-xs text-slate-500">
          采购员：{order.buyer}
        </span>
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-slate-400 hover:text-white"
            onClick={() => onView(order)}
            title="查看详情"
          >
            <Eye className="w-3.5 h-3.5" />
          </Button>

          {canEditOrder(statusKey) && onEdit && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-slate-400 hover:text-white"
              onClick={() => onEdit(order)}
              title="编辑"
            >
              <Edit3 className="w-3.5 h-3.5" />
            </Button>
          )}

          {canDeleteOrder(statusKey) && onDelete && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-red-400 hover:text-red-300"
              onClick={() => onDelete(order)}
              title="删除"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </Button>
          )}

          {["pending", "partial_received"].includes(statusKey) && onSubmit && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-blue-400 hover:text-blue-300"
              onClick={() => onSubmit(order)}
              title="确认收货"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
            </Button>
          )}

          {["pending", "partial_received"].includes(statusKey) && onApprove && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-emerald-400 hover:text-emerald-300"
              onClick={() => onApprove(order)}
              title="提交审批"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
            </Button>
          )}
        </div>
      </div>
    </motion.div>
  );
}
