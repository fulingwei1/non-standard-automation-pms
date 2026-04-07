



import { typeConfigs } from "./constants";

export default function CreateTemplateDialog({
  open,
  onOpenChange,
  templateForm,
  setTemplateForm,
  onConfirm,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>新建验收模板</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                模板名称 *
              </label>
              <Input
                value={templateForm.template_name}
                onChange={(e) =>
                  setTemplateForm({
                    ...templateForm,
                    template_name: e.target.value,
                  })
                }
                placeholder="请输入模板名称"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  模板类型
                </label>
                <Select
                  value={templateForm.template_type}
                  onValueChange={(val) =>
                    setTemplateForm({ ...templateForm, template_type: val })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(typeConfigs).map(([key, config]) => (
                      <SelectItem key={key} value={key || "unknown"}>
                        {config.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">版本</label>
                <Input
                  value={templateForm.version}
                  onChange={(e) =>
                    setTemplateForm({
                      ...templateForm,
                      version: e.target.value,
                    })
                  }
                  placeholder="1.0"
                />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">分类</label>
              <Input
                value={templateForm.category}
                onChange={(e) =>
                  setTemplateForm({
                    ...templateForm,
                    category: e.target.value,
                  })
                }
                placeholder="模板分类"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">描述</label>
              <textarea
                className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={templateForm.description}
                onChange={(e) =>
                  setTemplateForm({
                    ...templateForm,
                    description: e.target.value,
                  })
                }
                placeholder="模板描述..."
              />
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onConfirm}>创建</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
