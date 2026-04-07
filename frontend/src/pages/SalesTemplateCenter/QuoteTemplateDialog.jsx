


export default function QuoteTemplateDialog({
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
          <DialogTitle>新建报价模板</DialogTitle>
          <DialogDescription>
            定义基础信息与版本骨架，后续可继续扩展。
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 gap-2 items-center">
            <Label>模板编码</Label>
            <Input
              className="col-span-3"
              value={formData.template_code}
              onChange={update("template_code")}
            />
          </div>
          <div className="grid grid-cols-4 gap-2 items-center">
            <Label>模板名称</Label>
            <Input
              className="col-span-3"
              value={formData.template_name}
              onChange={update("template_name")}
            />
          </div>
          <div className="grid grid-cols-4 gap-2 items-center">
            <Label>版本号</Label>
            <Input
              className="col-span-3"
              value={formData.version_no}
              onChange={update("version_no")}
            />
          </div>
          <div className="grid grid-cols-4 gap-2 items-start">
            <Label>模板结构 JSON</Label>
            <Textarea
              className="col-span-3 min-h-[120px]"
              value={formData.sections}
              onChange={update("sections")}
            />
          </div>
          <div className="grid grid-cols-4 gap-2 items-start">
            <Label>定价规则 JSON</Label>
            <Textarea
              className="col-span-3 min-h-[120px]"
              value={formData.pricing_rules}
              onChange={update("pricing_rules")}
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
