import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../../../components/ui/dialog";
import { Button } from "../../../components/ui";
import { Badge } from "../../../components/ui/badge";

export function ClosureDetailDialog({ open, onOpenChange, closure }) {
  if (!closure) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>结项详情</DialogTitle>
        </DialogHeader>
        <div className="py-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-sm text-gray-500">项目名称</span>
              <p className="font-medium">{closure.project_name || "-"}</p>
            </div>
            <div>
              <span className="text-sm text-gray-500">状态</span>
              <p>
                <Badge variant={closure.status === "approved" ? "success" : "secondary"}>
                  {closure.status_display || closure.status || "-"}
                </Badge>
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-500">申请人</span>
              <p className="font-medium">{closure.applicant_name || "-"}</p>
            </div>
            <div>
              <span className="text-sm text-gray-500">申请时间</span>
              <p className="font-medium">{closure.created_at || "-"}</p>
            </div>
          </div>
          {closure.lessons && (
            <div>
              <span className="text-sm text-gray-500">经验教训</span>
              <p className="mt-1 text-sm">{closure.lessons}</p>
            </div>
          )}
          {closure.review_comment && (
            <div>
              <span className="text-sm text-gray-500">审核意见</span>
              <p className="mt-1 text-sm">{closure.review_comment}</p>
            </div>
          )}
        </div>
        <div className="flex justify-end">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
