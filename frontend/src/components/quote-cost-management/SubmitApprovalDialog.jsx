


export default function SubmitApprovalDialog({
  open,
  onOpenChange,
  approvalData,
  onApprovalDataChange,
  onSubmit,
  loading = false,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>提交成本审批</DialogTitle>
          <DialogDescription>提交报价成本进行审批</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>审批层级</Label>
            <Select
              value={approvalData.approval_level.toString()}
              onValueChange={(value) =>
                onApprovalDataChange({
                  ...approvalData,
                  approval_level: parseInt(value),
                })
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">
                  一级审批（销售经理）- 毛利率≥20%
                </SelectItem>
                <SelectItem value="2">
                  二级审批（销售总监）- 毛利率≥15%
                </SelectItem>
                <SelectItem value="3">三级审批（财务）- 最终决策</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>审批意见</Label>
            <Textarea
              value={approvalData.comment}
              onChange={(e) =>
                onApprovalDataChange({
                  ...approvalData,
                  comment: e.target.value,
                })
              }
              placeholder="请输入审批意见..."
              rows={4}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit} disabled={loading}>
            提交审批
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
