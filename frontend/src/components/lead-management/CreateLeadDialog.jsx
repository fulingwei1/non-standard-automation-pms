


export default function CreateLeadDialog({
  open,
  onOpenChange,
  formData,
  onDataChange,
  statusConfig,
  onCreate,
  loading = false,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>新建线索</DialogTitle>
          <DialogDescription>创建新的销售线索</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>客户名称 *</Label>
              <Input
                value={formData.customer_name}
                onChange={(e) =>
                  onDataChange({ ...formData, customer_name: e.target.value })
                }
                placeholder="请输入客户名称"
              />
            </div>
            <div>
              <Label>来源</Label>
              <Input
                value={formData.source}
                onChange={(e) =>
                  onDataChange({ ...formData, source: e.target.value })
                }
                placeholder="展会/转介绍/网络等"
              />
            </div>
            <div>
              <Label>行业</Label>
              <Input
                value={formData.industry}
                onChange={(e) =>
                  onDataChange({ ...formData, industry: e.target.value })
                }
                placeholder="请输入行业"
              />
            </div>
            <div>
              <Label>联系人</Label>
              <Input
                value={formData.contact_name}
                onChange={(e) =>
                  onDataChange({ ...formData, contact_name: e.target.value })
                }
                placeholder="请输入联系人"
              />
            </div>
            <div>
              <Label>联系电话</Label>
              <Input
                value={formData.contact_phone}
                onChange={(e) =>
                  onDataChange({ ...formData, contact_phone: e.target.value })
                }
                placeholder="请输入联系电话"
              />
            </div>
            <div>
              <Label>状态</Label>
              <select
                value={formData.status}
                onChange={(e) =>
                  onDataChange({ ...formData, status: e.target.value })
                }
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
              >
                {Object.entries(statusConfig).map(([key, config]) => (
                  <option key={key} value={key}>
                    {config.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <Label>需求摘要</Label>
            <Textarea
              value={formData.demand_summary}
              onChange={(e) =>
                onDataChange({ ...formData, demand_summary: e.target.value })
              }
              placeholder="请输入需求摘要"
              rows={4}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onCreate} disabled={loading}>
            创建
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
