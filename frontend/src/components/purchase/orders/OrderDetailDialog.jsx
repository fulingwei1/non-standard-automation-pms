/**
 * OrderDetailDialog - 采购订单详情对话框
 * 显示订单完整信息、采购项目列表、状态变更历史
 */

import { Package, Building2, Calendar, DollarSign } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody,
} from "../../ui/dialog";
import { Button } from "../../ui/button";
import { Label } from "../../ui/label";
import { Badge } from "../../ui/badge";
import { cn } from "../../../lib/utils";
import { ORDER_STATUS_CONFIGS, PurchaseOrderUtils } from "@/lib/constants/procurement";

export default function OrderDetailDialog({
  open,
  onOpenChange,
  order,
  onSubmitApproval,
}) {
  if (!order) {return null;}

  const statusConfig = ORDER_STATUS_CONFIGS[order.status] || ORDER_STATUS_CONFIGS.draft;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-slate-800/50 border border-slate-700/50">
        <DialogHeader>
          <DialogTitle className="text-white">采购订单详情</DialogTitle>
        </DialogHeader>

        <DialogBody className="space-y-6">
          {/* 订单基本信息 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-slate-400">订单编号</Label>
              <p className="text-white font-mono">{order.id}</p>
            </div>
            <div>
              <Label className="text-slate-400">供应商</Label>
              <p className="text-white">{order.supplierName}</p>
            </div>
            <div>
              <Label className="text-slate-400">项目</Label>
              <p className="text-white">{order.projectName}</p>
            </div>
            <div>
              <Label className="text-slate-400">状态</Label>
              <Badge className={cn(statusConfig?.color, "text-white")}>
                {statusConfig?.label}
              </Badge>
            </div>
            <div>
              <Label className="text-slate-400">采购员</Label>
              <p className="text-white">{order.buyer}</p>
            </div>
            <div>
              <Label className="text-slate-400">创建日期</Label>
              <p className="text-white">{PurchaseOrderUtils.formatDate(order.createdDate)}</p>
            </div>
            <div>
              <Label className="text-slate-400">预计到货</Label>
              <p className="text-white">{PurchaseOrderUtils.formatDate(order.expectedDate)}</p>
            </div>
            <div>
              <Label className="text-slate-400">订单金额</Label>
              <p className="text-white font-semibold">
                ¥{PurchaseOrderUtils.formatCurrency(order.totalAmount)}
              </p>
            </div>
          </div>

          {/* 采购项目列表 */}
          <div>
            <Label className="text-slate-400 mb-2 block">采购项目</Label>
            <div className="bg-slate-900/50 rounded-lg overflow-hidden border border-slate-700/50">
              <table className="w-full">
                <thead className="bg-slate-800/50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-slate-400">物料编码</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-slate-400">物料名称</th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-slate-400">数量</th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-slate-400">单价</th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-slate-400">小计</th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-slate-400">已收货</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50">
                  {order.items?.map((item, index) => (
                    <tr key={index}>
                      <td className="px-4 py-2 text-sm text-white">{item.code}</td>
                      <td className="px-4 py-2 text-sm text-white">{item.name}</td>
                      <td className="px-4 py-2 text-sm text-white text-right">{item.qty}</td>
                      <td className="px-4 py-2 text-sm text-white text-right">
                        ¥{PurchaseOrderUtils.formatCurrency(item.price)}
                      </td>
                      <td className="px-4 py-2 text-sm text-white text-right">
                        ¥{PurchaseOrderUtils.formatCurrency(item.qty * item.price)}
                      </td>
                      <td className="px-4 py-2 text-sm text-white text-right">{item.received}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 延期原因 */}
          {order.delayReason && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30">
              <Label className="text-red-300 mb-1 block">延期说明</Label>
              <p className="text-sm text-red-200">{order.delayReason}</p>
            </div>
          )}
        </DialogBody>

        <DialogFooter>
          {order.status === "draft" && onSubmitApproval && (
            <Button
              onClick={() => onSubmitApproval(order)}
              className="bg-emerald-500 hover:bg-emerald-600 text-white"
            >
              提交审批
            </Button>
          )}
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="bg-slate-700 border-slate-600 text-white"
          >
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
