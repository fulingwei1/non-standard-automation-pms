/**
 * Template Dialog - 套用装配模板对话框
 */





export function TemplateDialog({
  open,
  onOpenChange,
  templates,
  selectedTemplate,
  setSelectedTemplate,
  overwrite,
  setOverwrite,
  loading,
  onApplyTemplate,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>套用装配模板</DialogTitle>
          <DialogDescription>
            选择一个预设的装配模板应用到当前BOM
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label className="mb-2 block">选择模板</Label>
            <Select
              value={selectedTemplate || "unknown"}
              onValueChange={setSelectedTemplate}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择模板" />
              </SelectTrigger>
              <SelectContent>
                {(templates || []).map((tpl) => (
                  <SelectItem key={tpl.id} value={tpl.id.toString()}>
                    <div>
                      <span className="font-medium">{tpl.template_name}</span>
                      {tpl.equipment_type && (
                        <span className="text-slate-500 ml-2">
                          ({tpl.equipment_type})
                        </span>
                      )}
                      {tpl.is_default && (
                        <Badge variant="outline" className="ml-2">
                          默认
                        </Badge>
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label>覆盖已有配置</Label>
              <p className="text-sm text-slate-500">
                是否覆盖已经配置过的物料
              </p>
            </div>
            <Switch checked={overwrite} onCheckedChange={setOverwrite} />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button
            onClick={onApplyTemplate}
            disabled={loading || !selectedTemplate}
          >
            <FileDown className="w-4 h-4 mr-2" />
            应用模板
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
