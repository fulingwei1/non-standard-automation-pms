/**
 * DeleteConfirmDialog - 采购订单删除确认对话框
 * 确认删除操作的警告对话框
 */

import { AlertTriangle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody,
} from "../../../ui/dialog";
import { Button } from "../../../ui/button";

export default function DeleteConfirmDialog({
  open,
  onOpenChange,
  order,
  onConfirm,
}) {
  if (!order) return null;

  const handleConfirm = () => {
    onConfirm?.(order);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-slate-800/50 border border-slate-700/50">
        <DialogHeader>
          <DialogTitle className="text-white">确认删除</DialogTitle>
        </DialogHeader>

        <DialogBody className="text-center py-4">
          <AlertTriangle className="h-12 w-12 text-red-400 mx-auto mb-4" />
          <p className="text-white mb-2">
            确定要删除采购订单 <span className="font-mono font-semibold">{order.id}</span> 吗？
          </p>
          <p className="text-slate-400 text-sm">此操作不可撤销，请谨慎操作</p>

          {/* 附加信息 */}
          {order.supplierName && (
            <div className="mt-4 p-3 rounded-lg bg-slate-900/50 border border-slate-700/50">
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
        </DialogBody>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="bg-slate-700 border-slate-600 text-white"
          >
            取消
          </Button>
          <Button
            variant="destructive"
            onClick={handleConfirm}
            className="bg-red-500 hover:bg-red-600 text-white"
          >
            确认删除
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
