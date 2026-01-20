import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../ui/dialog";
import { Button } from "../ui/button";

export default function DeleteTemplateDialog({
  open,
  onOpenChange,
  template,
  onConfirm,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-surface-50 border-white/10">
        <DialogHeader>
          <DialogTitle className="text-white">确认删除</DialogTitle>
        </DialogHeader>
        <p className="text-slate-300">
          确定要删除模板 "{template?.template_name}" 吗？删除后无法恢复。
        </p>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="border-white/10 text-slate-300"
          >
            取消
          </Button>
          <Button onClick={onConfirm} className="bg-red-500 hover:bg-red-600">
            删除
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
