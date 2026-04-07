


export default function ConfirmDialog({
  open,
  onOpenChange,
  onConfirm,
  processing,
  autoFixTiming,
  autoFixMissing,
  timingIssues,
  missingIssues,
  cycleIssues,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Wrench className="w-5 h-5 text-blue-500" />
            确认执行依赖修复
          </DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <p className="text-slate-700">确定要执行以下依赖修复操作吗？</p>

            <div className="rounded-md bg-slate-50 p-4 space-y-2 text-sm">
              {autoFixTiming && (
                <div className="flex items-center gap-2">
                  <Network className="w-4 h-4 text-amber-500" />
                  <span>自动修复 {timingIssues.length} 个时序冲突</span>
                </div>
              )}

              {autoFixMissing && missingIssues.length > 0 && (
                <div className="flex items-center gap-2">
                  <Link2 className="w-4 h-4 text-blue-500" />
                  <span>自动移除 {missingIssues.length} 个缺失依赖</span>
                </div>
              )}

              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span>记录所有修复操作到进度日志</span>
              </div>
            </div>

            {cycleIssues.length > 0 && (
              <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm">
                <strong className="text-red-900">⚠️ 注意：</strong>
                循环依赖无法自动修复，需要手动处理。
              </div>
            )}
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onConfirm} disabled={processing}>
            {processing ? "修复中..." : "确认修复"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
