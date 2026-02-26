import { Button, Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, Input, Textarea } from "../ui";



export default function CompleteDispatchDialog({
  open,
  onOpenChange,
  completeData,
  onDataChange,
  onComplete,
  loading = false,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>完成派工单</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">实际工时</label>
            <Input
              type="number"
              value={completeData.actual_hours}
              onChange={(e) =>
                onDataChange({
                  ...completeData,
                  actual_hours: e.target.value,
                })
              }
              placeholder="小时"
            />
          </div>
          <div>
            <label className="text-sm font-medium">执行记录</label>
            <Textarea
              value={completeData.execution_notes}
              onChange={(e) =>
                onDataChange({
                  ...completeData,
                  execution_notes: e.target.value,
                })
              }
              placeholder="输入执行记录"
              rows={4}
            />
          </div>
          <div>
            <label className="text-sm font-medium">发现问题</label>
            <Textarea
              value={completeData.issues_found}
              onChange={(e) =>
                onDataChange({
                  ...completeData,
                  issues_found: e.target.value,
                })
              }
              placeholder="输入发现的问题"
              rows={3}
            />
          </div>
          <div>
            <label className="text-sm font-medium">解决方案</label>
            <Textarea
              value={completeData.solution_provided}
              onChange={(e) =>
                onDataChange({
                  ...completeData,
                  solution_provided: e.target.value,
                })
              }
              placeholder="输入解决方案"
              rows={3}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onComplete} disabled={loading}>
            完成
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
