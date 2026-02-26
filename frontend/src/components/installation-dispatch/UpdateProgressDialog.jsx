import { Button, Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, Input, Textarea } from "../ui";



export default function UpdateProgressDialog({
  open,
  onOpenChange,
  progressData,
  onDataChange,
  onUpdate,
  loading = false,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>更新进度</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">进度 (%)</label>
            <Input
              type="number"
              min="0"
              max="100"
              value={progressData.progress}
              onChange={(e) =>
                onDataChange({
                  ...progressData,
                  progress: parseInt(e.target.value) || 0,
                })
              }
            />
          </div>
          <div>
            <label className="text-sm font-medium">执行记录</label>
            <Textarea
              value={progressData.execution_notes}
              onChange={(e) =>
                onDataChange({
                  ...progressData,
                  execution_notes: e.target.value,
                })
              }
              placeholder="输入执行记录"
              rows={4}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onUpdate} disabled={loading}>
            更新进度
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
