/**
 * 阶段门审核对话框
 */



export function GateDialog({
  open, onOpenChange,
  gateData, setGateData,
  onSubmit,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>提交阶段门</DialogTitle>
          <DialogDescription>提交商机阶段门审核</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>阶段门状态 *</Label>
            <select
              value={gateData.gate_status}
              onChange={(e) =>
                setGateData({ ...gateData, gate_status: e.target.value })
              }
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
            >
              <option value="PASS">通过</option>
              <option value="REJECT">拒绝</option>
            </select>
          </div>
          <div>
            <Label>备注</Label>
            <Textarea
              value={gateData.remark}
              onChange={(e) =>
                setGateData({ ...gateData, remark: e.target.value })
              }
              placeholder="请输入备注"
              rows={3}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit}>提交</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
