


export default function AssignDispatchDialog({
  open,
  onOpenChange,
  assignData,
  onDataChange,
  users,
  isBatch = false,
  onAssign,
  loading = false,
}) {
  const technicians = users.filter((user) => user.role === "technician");

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isBatch ? "批量派工" : "指派派工单"}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">派工人员</label>
            <Select
              value={assignData.assigned_to_id}
              onValueChange={(value) =>
                onDataChange({ ...assignData, assigned_to_id: value })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="选择派工人员" />
              </SelectTrigger>
              <SelectContent>
                {technicians.map((user) => (
                  <SelectItem key={user.id} value={user.id}>
                    {user.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium">备注</label>
            <Textarea
              value={assignData.remark}
              onChange={(e) =>
                onDataChange({ ...assignData, remark: e.target.value })
              }
              placeholder="输入派工备注"
              rows={3}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onAssign} disabled={loading}>
            {isBatch ? "批量派工" : "派工"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
