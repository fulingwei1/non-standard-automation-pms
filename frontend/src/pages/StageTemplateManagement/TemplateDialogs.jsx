




function TemplateFormFields({ formData, onFormChange, disableCode = false }) {
  return (
    <>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>模板编码 {disableCode ? "" : "*"}</Label>
          <Input
            placeholder="如 STD_9_STAGE"
            value={formData.template_code}
            onChange={(e) => onFormChange("template_code", e.target.value.toUpperCase())}
            disabled={disableCode}
            className="bg-white/5 border-white/10"
          />
        </div>
        <div className="space-y-2">
          <Label>项目类型</Label>
          <Select
            value={formData.project_type}
            onValueChange={(v) => onFormChange("project_type", v)}
          >
            <SelectTrigger className="bg-white/5 border-white/10">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="STANDARD">标准项目</SelectItem>
              <SelectItem value="CUSTOM">定制项目</SelectItem>
              <SelectItem value="R&D">研发项目</SelectItem>
              <SelectItem value="MAINTENANCE">维保项目</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="space-y-2">
        <Label>模板名称 *</Label>
        <Input
          placeholder="如 标准九阶段流程"
          value={formData.template_name}
          onChange={(e) => onFormChange("template_name", e.target.value)}
          className="bg-white/5 border-white/10"
        />
      </div>
      <div className="space-y-2">
        <Label>模板描述</Label>
        <Textarea
          placeholder="描述该模板的用途和适用场景..."
          value={formData.description}
          onChange={(e) => onFormChange("description", e.target.value)}
          className="bg-white/5 border-white/10 min-h-[80px]"
        />
      </div>
    </>
  );
}

function ToggleSwitches({ formData, onFormChange, idPrefix }) {
  return (
    <div className="flex items-center gap-6">
      <div className="flex items-center gap-2">
        <Switch
          id={`${idPrefix}_is_default`}
          checked={formData.is_default}
          onCheckedChange={(v) => onFormChange("is_default", v)}
        />
        <Label htmlFor={`${idPrefix}_is_default`} className="cursor-pointer">
          设为默认
        </Label>
      </div>
      <div className="flex items-center gap-2">
        <Switch
          id={`${idPrefix}_is_active`}
          checked={formData.is_active}
          onCheckedChange={(v) => onFormChange("is_active", v)}
        />
        <Label htmlFor={`${idPrefix}_is_active`} className="cursor-pointer">
          启用
        </Label>
      </div>
    </div>
  );
}

export function CreateDialog({ open, onOpenChange, formData, onFormChange, onCreate }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5 text-violet-400" />
            新建阶段模板
          </DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <TemplateFormFields formData={formData} onFormChange={onFormChange} />
          <ToggleSwitches formData={formData} onFormChange={onFormChange} idPrefix="create" />
        </DialogBody>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onCreate}>创建</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function EditDialog({ open, onOpenChange, formData, onFormChange, onUpdate }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Edit3 className="h-5 w-5 text-violet-400" />
            编辑阶段模板
          </DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <TemplateFormFields formData={formData} onFormChange={onFormChange} disableCode />
          <ToggleSwitches formData={formData} onFormChange={onFormChange} idPrefix="edit" />
        </DialogBody>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onUpdate}>保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function CopyDialog({ open, onOpenChange, formData, onFormChange, onCopy, selectedTemplate }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Copy className="h-5 w-5 text-violet-400" />
            复制模板
          </DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <p className="text-sm text-slate-400">
            正在复制模板 <span className="text-white font-medium">{selectedTemplate?.template_name}</span>
          </p>
          <div className="space-y-2">
            <Label>新模板编码 *</Label>
            <Input
              value={formData.template_code}
              onChange={(e) => onFormChange("template_code", e.target.value.toUpperCase())}
              className="bg-white/5 border-white/10"
            />
          </div>
          <div className="space-y-2">
            <Label>新模板名称 *</Label>
            <Input
              value={formData.template_name}
              onChange={(e) => onFormChange("template_name", e.target.value)}
              className="bg-white/5 border-white/10"
            />
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onCopy}>复制</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function TemplateDeleteDialog({ open, onOpenChange, selectedTemplate, onConfirm }) {
  return (
    <DeleteConfirmDialog
      open={open}
      onOpenChange={onOpenChange}
      title="确认删除"
      description={`确定要删除模板 "${selectedTemplate?.template_name}" 吗？`}
      confirmText="确认删除"
      onConfirm={onConfirm}
    >
      <p className="text-sm text-slate-500 mt-2">
        此操作不可撤销，所有相关的阶段和节点定义也将被删除。
      </p>
    </DeleteConfirmDialog>
  );
}
