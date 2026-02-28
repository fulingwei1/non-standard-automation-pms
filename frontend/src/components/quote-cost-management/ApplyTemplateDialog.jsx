

import { formatCurrency } from "../../lib/utils";
import { Button, Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, Label, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui";

export default function ApplyTemplateDialog({
  open,
  onOpenChange,
  costTemplates,
  selectedTemplate,
  onTemplateSelect,
  onApply,
  loading = false,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>应用成本模板</DialogTitle>
          <DialogDescription>选择成本模板应用到当前报价</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>选择模板</Label>
            <Select
              value={selectedTemplate?.id?.toString()}
              onValueChange={(value) => {
                const template = (costTemplates || []).find(
                  (t) => t.id.toString() === value
                );
                onTemplateSelect(template);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择成本模板" />
              </SelectTrigger>
              <SelectContent>
                {(costTemplates || []).map((template) => (
                  <SelectItem
                    key={template.id}
                    value={template.id.toString()}
                  >
                    {template.template_name} ({template.template_code})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedTemplate && (
            <div className="border border-slate-700 rounded-lg p-4">
              <div className="text-sm space-y-1">
                <div>
                  <strong>模板名称:</strong> {selectedTemplate.template_name}
                </div>
                <div>
                  <strong>模板类型:</strong> {selectedTemplate.template_type}
                </div>
                <div>
                  <strong>适用设备:</strong>{" "}
                  {selectedTemplate.equipment_type || "-"}
                </div>
                <div>
                  <strong>总成本:</strong>{" "}
                  {formatCurrency(selectedTemplate.total_cost || 0)}
                </div>
                {selectedTemplate.description && (
                  <div>
                    <strong>说明:</strong> {selectedTemplate.description}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onApply} disabled={!selectedTemplate || loading}>
            应用模板
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
