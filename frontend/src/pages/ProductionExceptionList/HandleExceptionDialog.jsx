/**
 * HandleExceptionDialog — form for recording a handling plan and result
 * for an in-progress production exception.
 */



export function HandleExceptionDialog({
  open,
  onOpenChange,
  selectedException,
  handleData,
  setHandleData,
  onSubmit,
}) {
  const update = (patch) => setHandleData((prev) => ({ ...prev, ...patch }));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>处理生产异常</DialogTitle>
        </DialogHeader>
        <DialogBody>
          {selectedException && (
            <div className="space-y-4">
              <div>
                <div className="text-sm text-slate-500 mb-1">异常标题</div>
                <div className="font-medium">{selectedException.title}</div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  处理方案
                </label>
                <textarea
                  className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={handleData.handle_plan}
                  onChange={(e) => update({ handle_plan: e.target.value })}
                  placeholder="填写处理方案..."
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  处理结果
                </label>
                <textarea
                  className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={handleData.handle_result}
                  onChange={(e) => update({ handle_result: e.target.value })}
                  placeholder="填写处理结果..."
                />
              </div>
            </div>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit}>保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
