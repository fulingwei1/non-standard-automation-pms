import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../ui/dialog";
import { Button } from "../ui/button";
import { Label } from "../ui/label";
import { Badge } from "../ui/badge";

export default function TemplateDetailDialog({
  open,
  onOpenChange,
  template,
  categoryConfigs,
  issueTypeConfigs,
  formatDate,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-surface-50 border-white/10 max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-white">模板详情</DialogTitle>
        </DialogHeader>
        {template && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-400">模板名称</Label>
                <p className="text-white">{template.template_name}</p>
              </div>
              <div>
                <Label className="text-slate-400">模板编码</Label>
                <p className="text-white">{template.template_code}</p>
              </div>
              <div>
                <Label className="text-slate-400">分类</Label>
                <Badge
                  className={
                    categoryConfigs[template.category]?.color || "bg-slate-500"
                  }
                >
                  {categoryConfigs[template.category]?.label ||
                    template.category}
                </Badge>
              </div>
              <div>
                <Label className="text-slate-400">问题类型</Label>
                <Badge
                  className={
                    issueTypeConfigs[template.issue_type]?.color ||
                    "bg-slate-500"
                  }
                >
                  {issueTypeConfigs[template.issue_type]?.label ||
                    template.issue_type}
                </Badge>
              </div>
              <div>
                <Label className="text-slate-400">使用次数</Label>
                <p className="text-white">{template.usage_count || 0}</p>
              </div>
              <div>
                <Label className="text-slate-400">最后使用时间</Label>
                <p className="text-white">
                  {template.last_used_at
                    ? formatDate(template.last_used_at)
                    : "未使用"}
                </p>
              </div>
            </div>
            <div>
              <Label className="text-slate-400">标题模板</Label>
              <p className="text-white bg-surface-100 p-2 rounded">
                {template.title_template}
              </p>
            </div>
            {template.description_template && (
              <div>
                <Label className="text-slate-400">描述模板</Label>
                <p className="text-white bg-surface-100 p-2 rounded whitespace-pre-wrap">
                  {template.description_template}
                </p>
              </div>
            )}
            {template.solution_template && (
              <div>
                <Label className="text-slate-400">解决方案模板</Label>
                <p className="text-white bg-surface-100 p-2 rounded whitespace-pre-wrap">
                  {template.solution_template}
                </p>
              </div>
            )}
          </div>
        )}
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="border-white/10 text-slate-300"
          >
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
