

import { typeConfigs } from "./constants";

function TemplateItemCard({ item }) {
  return (
    <div className="border rounded-lg p-3">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="font-medium">{item.item_name}</div>
          <div className="text-xs text-slate-500 mt-1">
            {item.item_code}{" "}
            {item.is_key_item && (
              <Badge variant="destructive" className="ml-1">
                关键项
              </Badge>
            )}
          </div>
          {item.acceptance_criteria && (
            <div className="text-xs text-slate-600 mt-1">
              验收标准: {item.acceptance_criteria}
            </div>
          )}
        </div>
        {item.is_required && <Badge className="bg-blue-500">必检</Badge>}
      </div>
    </div>
  );
}

export default function TemplateDetailDialog({
  open,
  onOpenChange,
  selectedTemplate,
  templateItems,
  onManageItems,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {selectedTemplate?.template_name} - 模板详情
          </DialogTitle>
        </DialogHeader>
        <DialogBody>
          {selectedTemplate && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">模板名称</div>
                  <div>{selectedTemplate.template_name}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">模板类型</div>
                  <Badge
                    className={
                      typeConfigs[selectedTemplate.template_type]?.color
                    }
                  >
                    {typeConfigs[selectedTemplate.template_type]?.label}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">分类</div>
                  <div>{selectedTemplate.category || "-"}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">版本</div>
                  <div>{selectedTemplate.version || "1.0"}</div>
                </div>
              </div>
              {selectedTemplate.description && (
                <div>
                  <div className="text-sm text-slate-500 mb-1">描述</div>
                  <div>{selectedTemplate.description}</div>
                </div>
              )}
              <div>
                <div className="text-sm text-slate-500 mb-2">检查项列表</div>
                <div className="space-y-2">
                  {templateItems.length === 0 ? (
                    <div className="text-center py-4 text-slate-400">
                      暂无检查项
                    </div>
                  ) : (
                    templateItems.map((item) => (
                      <TemplateItemCard key={item.id} item={item} />
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
          {selectedTemplate && (
            <Button onClick={() => onManageItems(selectedTemplate.id)}>
              <CheckSquare className="w-4 h-4 mr-2" />
              管理检查项
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
