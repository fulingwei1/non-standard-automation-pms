/**
 * ReceiveGoodsDialog - 采购订单收货确认对话框
 * 用于确认物料收货，记录收货日期和备注
 */

import { useState as _useState, useEffect } from "react";
import { Package, CheckCircle2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody } from
"../../ui/dialog";
import { Button } from "../../ui/button";
import { Label } from "../../ui/label";
import { Input } from "../../ui/input";
import { Textarea } from "../../ui/textarea";
import { Badge } from "../../ui/badge";
import { cn } from "../../../lib/utils";

export default function ReceiveGoodsDialog({
  open,
  onOpenChange,
  order,
  receiveData = { received_date: "", notes: "" },
  onChangeReceiveData,
  onConfirm
}) {
  // 初始化收货日期为今天
  useEffect(() => {
    if (open && !receiveData.received_date) {
      const today = new Date().toISOString().split("T")[0];
      onChangeReceiveData?.({ ...receiveData, received_date: today });
    }
  }, [open]);

  if (!order) {return null;}

  const handleConfirm = () => {
    onConfirm?.(order, receiveData);
    onOpenChange(false);
  };

  // 计算收货进度
  const totalItems = order.itemCount || order.items?.length || 0;
  const receivedItems = order.receivedCount || 0;
  const progress = totalItems > 0 ? receivedItems / totalItems * 100 : 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] bg-slate-800/50 border border-slate-700/50">
        <DialogHeader>
          <DialogTitle className="text-white">确认收货</DialogTitle>
        </DialogHeader>

        <DialogBody className="space-y-4">
          {/* 订单信息摘要 */}
          <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-700/50">
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono text-white">{order.id}</span>
              <Badge className="bg-blue-500/20 text-blue-300 border border-blue-500/30">
                {receivedItems}/{totalItems} 项已收货
              </Badge>
            </div>
            <p className="text-sm text-slate-400">{order.supplierName}</p>
            {order.projectName &&
            <p className="text-sm text-slate-400 mt-1">项目：{order.projectName}</p>
            }

            {/* 进度条 */}
            {totalItems > 0 &&
            <div className="mt-3">
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                  className={cn(
                    "h-full rounded-full transition-all",
                    progress >= 100 ?
                    "bg-emerald-500" :
                    progress >= 50 ?
                    "bg-blue-500" :
                    "bg-amber-500"
                  )}
                  style={{ width: `${Math.min(progress, 100)}%` }} />

                </div>
            </div>
            }
          </div>

          {/* 待收货物料列表 */}
          {order.items && order.items?.length > 0 &&
          <div>
              <Label className="text-slate-400 mb-2 block">待收货物料</Label>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {order.items.
              filter((item) => (item.received || 0) < (item.qty || 0)).
              map((item, index) =>
              <div
                key={index}
                className="flex items-center justify-between p-2 rounded bg-slate-900/30 border border-slate-700/30">

                      <div className="flex-1">
                        <p className="text-sm text-white">{item.name || item.code}</p>
                        <p className="text-xs text-slate-500">
                          已收货：{item.received || 0} / {item.qty || 0}
                        </p>
                      </div>
                      <CheckCircle2 className="w-5 h-5 text-amber-400" />
              </div>
              )}
              </div>
          </div>
          }

          {/* 收货日期 */}
          <div>
            <Label className="text-slate-400">收货日期</Label>
            <Input
              type="date"
              value={receiveData.received_date}
              onChange={(e) =>
              onChangeReceiveData?.({ ...receiveData, received_date: e.target.value })
              }
              className="bg-slate-900 border-slate-700 text-white" />

          </div>

          {/* 收货备注 */}
          <div>
            <Label className="text-slate-400">收货备注</Label>
            <Textarea
              value={receiveData.notes}
              onChange={(e) =>
              onChangeReceiveData?.({ ...receiveData, notes: e.target.value })
              }
              placeholder="记录收货情况、物料状态、质量问题等..."
              className="bg-slate-900 border-slate-700 text-white placeholder-slate-400"
              rows={3} />

          </div>
        </DialogBody>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="bg-slate-700 border-slate-600 text-white">

            取消
          </Button>
          <Button
            onClick={handleConfirm}
            className="bg-emerald-500 hover:bg-emerald-600 text-white"
            disabled={!receiveData.received_date}>

            <CheckCircle2 className="w-4 h-4 mr-2" />
            确认收货
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>);

}