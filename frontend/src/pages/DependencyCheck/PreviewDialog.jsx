import React from "react";
import { Eye } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody,
} from "../../components/ui/dialog";
import { Button } from "../../components/ui/button";

export default function PreviewDialog({
  open,
  onOpenChange,
  previewData,
  onConfirm,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Eye className="w-5 h-5" />
            依赖修复预览
          </DialogTitle>
        </DialogHeader>
        <DialogBody>
          {previewData ? (
            <div className="space-y-6">
              {/* 循环依赖预览 */}
              {previewData.has_cycle && (
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 mb-3">
                    循环依赖（需手动处理）
                  </h4>
                  <div className="space-y-2">
                    {(previewData.cycle_paths || []).map((cycle, idx) => (
                      <div
                        key={idx}
                        className="rounded-md bg-red-50 border border-red-200 p-3"
                      >
                        <div className="text-sm text-red-800">
                          循环 {idx + 1}: {cycle.join(" → ")}
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="rounded-md bg-amber-50 border border-amber-200 p-3 text-sm mt-2">
                    <strong className="text-amber-900">
                      ⚠️ 循环依赖无法自动修复，请在修复其他问题后手动调整。
                    </strong>
                  </div>
                </div>
              )}

              {/* 修复操作预览 */}
              <div>
                <h4 className="text-sm font-semibold text-slate-900 mb-3">
                  将要执行的修复操作
                </h4>
                <div className="space-y-2">
                  {previewData.preview_actions?.will_fix_timing > 0 && (
                    <div className="rounded-md bg-amber-50 border border-amber-200 p-3">
                      <div className="font-medium text-amber-900 mb-1">
                        将修复 {previewData.preview_actions.will_fix_timing} 个时序冲突
                      </div>
                      <div className="text-xs text-amber-700">
                        自动调整任务计划时间以解决时序冲突
                      </div>
                    </div>
                  )}

                  {previewData.preview_actions?.will_remove_missing > 0 && (
                    <div className="rounded-md bg-blue-50 border border-blue-200 p-3">
                      <div className="font-medium text-blue-900 mb-1">
                        将移除 {previewData.preview_actions.will_remove_missing} 个缺失依赖
                      </div>
                      <div className="text-xs text-blue-700">
                        删除指向不存在任务的依赖关系
                      </div>
                    </div>
                  )}

                  {previewData.preview_actions?.will_skip_cycles > 0 && (
                    <div className="rounded-md bg-slate-100 border border-slate-300 p-3">
                      <div className="font-medium text-slate-900 mb-1">
                        跳过 {previewData.preview_actions.will_skip_cycles} 个循环依赖
                      </div>
                      <div className="text-xs text-slate-700">
                        循环依赖需手动处理
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">加载预览数据中...</div>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onConfirm}>确认修复</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
