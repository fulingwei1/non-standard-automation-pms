


export default function RuleSetDialog({
  open,
  onOpenChange,
  formData,
  setFormData,
  onSubmit,
}) {
  const update = (field) => (e) =>
    setFormData((prev) => ({ ...prev, [field]: e.target.value }));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>新增 CPQ 规则集</DialogTitle>
          <DialogDescription>
            定义资源负载、价格矩阵与审批阈值。
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 gap-2 items-center">
            <Label>规则编码</Label>
            <Input
              className="col-span-3"
              value={formData.rule_code}
              onChange={update("rule_code")}
            />
          </div>
          <div className="grid grid-cols-4 gap-2 items-center">
            <Label>规则名称</Label>
            <Input
              className="col-span-3"
              value={formData.rule_name}
              onChange={update("rule_name")}
            />
          </div>
          <div className="grid grid-cols-4 gap-2 items-center">
            <Label>基准价格</Label>
            <Input
              type="number"
              className="col-span-3"
              value={formData.base_price}
              onChange={update("base_price")}
            />
          </div>
          <div className="grid grid-cols-4 gap-2 items-start">
            <Label>配置项 JSON</Label>
            <Textarea
              className="col-span-3 min-h-[120px]"
              value={formData.config_schema}
              onChange={update("config_schema")}
            />
          </div>
          <div className="grid grid-cols-4 gap-2 items-start">
            <Label>定价矩阵 JSON</Label>
            <Textarea
              className="col-span-3 min-h-[120px]"
              value={formData.pricing_matrix}
              onChange={update("pricing_matrix")}
            />
          </div>
          <div className="grid grid-cols-4 gap-2 items-start">
            <Label>审批阈值 JSON</Label>
            <Textarea
              className="col-span-3 min-h-[120px]"
              value={formData.approval_threshold}
              onChange={update("approval_threshold")}
            />
          </div>
        </div>
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
