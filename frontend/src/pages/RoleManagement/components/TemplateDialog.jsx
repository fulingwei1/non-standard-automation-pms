/**
 * 从模板创建角色对话框组件
 */

import { DATA_SCOPE_MAP } from '../constants';

export default function TemplateDialog({
  open,
  onOpenChange,
  templateForm,
  setTemplateForm,
  onSubmit,
  templates,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>从模板创建角色</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">选择模板 *</label>
              <Select
                value={templateForm.template_id?.toString() || ''}
                onValueChange={(v) => setTemplateForm({ ...templateForm, template_id: parseInt(v) })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择角色模板" />
                </SelectTrigger>
                <SelectContent>
                  {(templates || []).map((tpl) => (
                    <SelectItem key={tpl.id} value={tpl.id.toString()}>
                      {tpl.template_name}
                      <span className="text-slate-400 ml-2">
                        ({DATA_SCOPE_MAP[tpl.data_scope]?.label || tpl.data_scope})
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">角色编码 *</label>
              <Input
                value={templateForm.role_code}
                onChange={(e) => setTemplateForm({ ...templateForm, role_code: e.target.value })}
                placeholder="如: SALES_MANAGER_NORTH"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">角色名称 *</label>
              <Input
                value={templateForm.role_name}
                onChange={(e) => setTemplateForm({ ...templateForm, role_name: e.target.value })}
                placeholder="如: 华北区销售经理"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">描述</label>
              <Input
                value={templateForm.description}
                onChange={(e) => setTemplateForm({ ...templateForm, description: e.target.value })}
                placeholder="角色描述"
              />
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit}>
            <FileText className="w-4 h-4 mr-2" />
            创建角色
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
