



import { typeConfigs } from "./constants";

export default function CreatePlanDialog({
  open,
  onOpenChange,
  newPlan,
  setNewPlan,
  onSubmit,
  projects,
  workshops,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>新建生产计划</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            {/* Plan name */}
            <div>
              <label className="text-sm font-medium mb-2 block">计划名称 *</label>
              <Input
                value={newPlan.plan_name}
                onChange={(e) => setNewPlan({ ...newPlan, plan_name: e.target.value })}
                placeholder="请输入计划名称"
              />
            </div>

            {/* Type + Project */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">计划类型</label>
                <Select
                  value={newPlan.plan_type}
                  onValueChange={(val) => setNewPlan({ ...newPlan, plan_type: val })}
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
                <label className="text-sm font-medium mb-2 block">项目</label>
                <Select
                  value={newPlan.project_id?.toString() || ""}
                  onValueChange={(val) =>
                    setNewPlan({ ...newPlan, project_id: val ? parseInt(val) : null })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择项目" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">无</SelectItem>
                    {(projects || []).map((proj) => (
                      <SelectItem key={proj.id} value={proj.id.toString()}>
                        {proj.project_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Workshop (only for WORKSHOP type) */}
            {newPlan.plan_type === "WORKSHOP" && (
              <div>
                <label className="text-sm font-medium mb-2 block">车间</label>
                <Select
                  value={newPlan.workshop_id?.toString() || ""}
                  onValueChange={(val) =>
                    setNewPlan({ ...newPlan, workshop_id: val ? parseInt(val) : null })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择车间" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">无</SelectItem>
                    {(workshops || []).map((ws) => (
                      <SelectItem key={ws.id} value={ws.id.toString()}>
                        {ws.workshop_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Start + End dates */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">计划开始日期 *</label>
                <Input
                  type="date"
                  value={newPlan.plan_start_date}
                  onChange={(e) =>
                    setNewPlan({ ...newPlan, plan_start_date: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">计划结束日期 *</label>
                <Input
                  type="date"
                  value={newPlan.plan_end_date}
                  onChange={(e) =>
                    setNewPlan({ ...newPlan, plan_end_date: e.target.value })
                  }
                />
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="text-sm font-medium mb-2 block">描述</label>
              <textarea
                className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={newPlan.description}
                onChange={(e) =>
                  setNewPlan({ ...newPlan, description: e.target.value })
                }
                placeholder="计划描述..."
              />
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit}>创建</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
