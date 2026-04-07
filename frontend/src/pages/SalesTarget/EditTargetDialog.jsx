


export default function EditTargetDialog({
  open,
  onOpenChange,
  formData,
  setFormData,
  onUpdate,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>编辑销售目标</DialogTitle>
          <DialogDescription>修改目标值和状态</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>目标值</Label>
            <Input
              type="number"
              value={formData.target_value}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  target_value: e.target.value,
                }))
              }
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>项目经理小组</Label>
              <Input value={formData.manager_group} onChange={(e)=>setFormData((prev)=>({...prev, manager_group: e.target.value}))} placeholder="如：华南PM一组" />
            </div>
            <div>
              <Label>总监小组</Label>
              <Input value={formData.director_group} onChange={(e)=>setFormData((prev)=>({...prev, director_group: e.target.value}))} placeholder="如：华南销售总监组" />
            </div>
            <div>
              <Label>行业</Label>
              <Input value={formData.industry} onChange={(e)=>setFormData((prev)=>({...prev, industry: e.target.value}))} placeholder="如：汽车电子" />
            </div>
            <div>
              <Label>大区</Label>
              <Input value={formData.region} onChange={(e)=>setFormData((prev)=>({...prev, region: e.target.value}))} placeholder="如：华东" />
            </div>
            <div className="md:col-span-2">
              <Label>目标客户</Label>
              <Input value={formData.target_customer} onChange={(e)=>setFormData((prev)=>({...prev, target_customer: e.target.value}))} placeholder="如：比亚迪/立讯" />
            </div>
          </div>
          <div>
            <Label>描述</Label>
            <Input
              value={formData.description}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  description: e.target.value,
                }))
              }
            />
          </div>
          <div>
            <Label>状态</Label>
            <Select
              value={formData.status}
              onValueChange={(value) =>
                setFormData((prev) => ({ ...prev, status: value }))
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ACTIVE">进行中</SelectItem>
                <SelectItem value="COMPLETED">已完成</SelectItem>
                <SelectItem value="CANCELLED">已取消</SelectItem>
              </SelectContent>
            </Select>
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
