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

export function LessonsClosureDialog({ open, onOpenChange, onSubmit, closure }) {
  const [lessons, setLessons] = useState("");

  const handleSubmit = () => {
    onSubmit?.({ lessons });
    setLessons("");
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>经验教训总结</DialogTitle>
        </DialogHeader>
        <div className="py-4 space-y-4">
          <div>
            <label className="text-sm font-medium">经验教训</label>
            <Textarea
              value={lessons}
              onChange={(e) => setLessons(e.target.value)}
              placeholder="请总结项目的经验教训..."
              rows={6}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
