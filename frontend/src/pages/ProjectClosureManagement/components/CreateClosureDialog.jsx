import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../../../components/ui/dialog";
import { Button } from "../../../components/ui";

export function CreateClosureDialog({ open, onOpenChange, onSubmit, project }) {
  const handleSubmit = () => {
    onSubmit?.({});
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>创建结项申请</DialogTitle>
        </DialogHeader>
        <div className="py-4">
          <p className="text-sm text-gray-600">
            确认为项目 {project?.name || project?.project_name} 创建结项申请？
          </p>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>确认创建</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
