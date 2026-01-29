import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../../../components/ui/dialog";
import { Button } from "../../../components/ui";
import { Textarea } from "../../../components/ui/textarea";

export function ReviewClosureDialog({ open, onOpenChange, onSubmit }) {
  const [comment, setComment] = useState("");

  const handleSubmit = (approved) => {
    onSubmit?.({ approved, comment });
    setComment("");
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>结项审核</DialogTitle>
        </DialogHeader>
        <div className="py-4 space-y-4">
          <div>
            <label className="text-sm font-medium">审核意见</label>
            <Textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="请输入审核意见..."
              rows={4}
            />
          </div>
        </div>
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button variant="destructive" onClick={() => handleSubmit(false)}>
            驳回
          </Button>
          <Button onClick={() => handleSubmit(true)}>通过</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
