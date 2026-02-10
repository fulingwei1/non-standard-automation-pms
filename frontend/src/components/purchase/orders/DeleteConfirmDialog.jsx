/**
 * DeleteConfirmDialog - 采购订单删除确认对话框
 * 基于通用 DeleteConfirmDialog 的采购订单适配
 */

import React from "react";
import DeleteConfirmDialog from "../../common/DeleteConfirmDialog";

export default function PurchaseOrderDeleteConfirmDialog({
  open,
  onOpenChange,
 order,
 onConfirm,
}) {
 if (!order) {return null;}

 return (
  <DeleteConfirmDialog
 open={open}
  onOpenChange={onOpenChange}
 title="确认删除"
 description={`确定要删除采购订单 ${order.id} 吗？此操作不可撤销，请谨慎操作`}
  onConfirm={() => onConfirm?.(order)}
  >
  {order.supplierName && (
  <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-700/50">
 <p className="text-sm text-slate-400">
   供应商：<span className="text-white">{order.supplierName}</span>
   </p>
  {order.projectName && (
  <p className="text-sm text-slate-400 mt-1">
  项目：<span className="text-white">{order.projectName}</span>
   </p>
  )}
  {order.totalAmount && (
  <p className="text-sm text-slate-400 mt-1">
  金额：<span className="text-white">¥{order.totalAmount.toLocaleString()}</span>
  </p>
  )}
   </div>
  )}
  </DeleteConfirmDialog>
 );
}
