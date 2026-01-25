import React from "react";
import {
  Button,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Label,
  Textarea,
} from "../../components/ui";

export default function EditLeadDialog({
  open,
  onOpenChange,
  formData,
  setFormData,
  statusConfig,
  onUpdate,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>编辑线索</DialogTitle>
          <DialogDescription>更新线索信息</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>客户名称 *</Label>
              <Input
                value={formData.customer_name}
                onChange={(e) =>
                  setFormData({ ...formData, customer_name: e.target.value })
                }
              />
            </div>
            <div>
              <Label>来源</Label>
              <Input
                value={formData.source}
                onChange={(e) =>
                  setFormData({ ...formData, source: e.target.value })
                }
              />
            </div>
            <div>
              <Label>行业</Label>
              <Input
                value={formData.industry}
                onChange={(e) =>
                  setFormData({ ...formData, industry: e.target.value })
                }
              />
            </div>
            <div>
              <Label>联系人</Label>
              <Input
                value={formData.contact_name}
                onChange={(e) =>
                  setFormData({ ...formData, contact_name: e.target.value })
                }
              />
            </div>
            <div>
              <Label>联系电话</Label>
              <Input
                value={formData.contact_phone}
                onChange={(e) =>
                  setFormData({ ...formData, contact_phone: e.target.value })
                }
              />
            </div>
            <div>
              <Label>状态</Label>
              <select
                value={formData.status}
                onChange={(e) =>
                  setFormData({ ...formData, status: e.target.value })
                }
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
              >
                {["NEW", "CONTACTED", "QUALIFIED", "LOST", "CONVERTED"].map(
                  (key) => (
                    <option key={key} value={key}>
                      {statusConfig[key]?.label || key}
                    </option>
                  )
                )}
              </select>
            </div>
          </div>
          <div>
            <Label>需求摘要</Label>
            <Textarea
              value={formData.demand_summary}
              onChange={(e) =>
                setFormData({ ...formData, demand_summary: e.target.value })
              }
              rows={4}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onUpdate}>保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
