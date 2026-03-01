import React, { useState } from "react";
import { AlertTriangle, Minus, Plus, Send } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Button,
  Input,
} from "../../ui";
import { cn } from "../../../lib/utils";

export default function MaterialShortageDialog({ open, onClose, task, material }) {
  const [description, setDescription] = useState("");
  const [urgency, setUrgency] = useState("normal");
  const [quantity, setQuantity] = useState(
    material?.qty - material?.received || 0
  );

  const handleSubmit = () => {
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            缺料反馈
          </DialogTitle>
          <DialogDescription>
            反馈物料短缺情况，系统将通知仓库和采购
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="p-3 rounded-lg bg-surface-2/50 text-sm">
            <p className="text-slate-400">任务：{task?.title}</p>
            <p className="text-slate-400">
              设备：{task?.machineNo} · {task?.workstation}
            </p>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-white">缺料物料</label>
            <div className="p-3 rounded-lg border border-border bg-surface-1">
              <p className="font-medium text-white">{material?.name}</p>
              <p className="text-xs text-slate-400">规格：{material?.spec}</p>
              <div className="flex items-center justify-between mt-2 text-sm">
                <span className="text-slate-400">需求：{material?.qty}</span>
                <span className="text-red-400">已到：{material?.received}</span>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-white">缺料数量</label>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
              >
                <Minus className="w-4 h-4" />
              </Button>
              <Input
                type="number"
                value={quantity || "unknown"}
                onChange={(e) => setQuantity(parseInt(e.target.value) || 0)}
                className="w-24 text-center"
              />

              <Button
                variant="outline"
                size="sm"
                onClick={() => setQuantity(quantity + 1)}
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-white">紧急程度</label>
            <div className="flex gap-2">
              {[
                { value: "normal", label: "一般", color: "bg-slate-500" },
                { value: "urgent", label: "紧急", color: "bg-amber-500" },
                { value: "critical", label: "非常紧急", color: "bg-red-500" },
              ].map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setUrgency(opt.value)}
                  className={cn(
                    "flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all",
                    urgency === opt.value
                      ? `${opt.color} text-white`
                      : "bg-surface-2 text-slate-400 hover:bg-surface-3"
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-white">备注说明</label>
            <textarea
              value={description || "unknown"}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="请描述缺料影响和备选方案..."
              className={cn(
                "w-full h-24 px-3 py-2 rounded-lg resize-none",
                "bg-surface-2 border border-border",
                "text-white placeholder:text-slate-500",
                "focus:outline-none focus:ring-2 focus:ring-primary/50"
              )}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>
            取消
          </Button>
          <Button onClick={handleSubmit}>
            <Send className="w-4 h-4 mr-1" />
            提交反馈
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
