



import { priorityConfigs } from "./statusConstants";

export default function CreateOrderDialog({
  open,
  onOpenChange,
  newOrder,
  setNewOrder,
  projects,
  onSubmit,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>新建工单</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                任务名称 *
              </label>
              <Input
                value={newOrder.task_name}
                onChange={(e) =>
                  setNewOrder({ ...newOrder, task_name: e.target.value })
                }
                placeholder="请输入任务名称"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  项目 *
                </label>
                <Select
                  value={newOrder.project_id?.toString() || ""}
                  onValueChange={(val) =>
                    setNewOrder({
                      ...newOrder,
                      project_id: val ? parseInt(val) : null,
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择项目" />
                  </SelectTrigger>
                  <SelectContent>
                    {(projects || []).map((proj) => (
                      <SelectItem key={proj.id} value={proj.id.toString()}>
                        {proj.project_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  任务类型
                </label>
                <Select
                  value={newOrder.task_type}
                  onValueChange={(val) =>
                    setNewOrder({ ...newOrder, task_type: val })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ASSEMBLY">装配</SelectItem>
                    <SelectItem value="MACHINING">机加工</SelectItem>
                    <SelectItem value="WELDING">焊接</SelectItem>
                    <SelectItem value="PAINTING">喷涂</SelectItem>
                    <SelectItem value="OTHER">其他</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  物料名称
                </label>
                <Input
                  value={newOrder.material_name}
                  onChange={(e) =>
                    setNewOrder({
                      ...newOrder,
                      material_name: e.target.value,
                    })
                  }
                  placeholder="物料名称"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">规格</label>
                <Input
                  value={newOrder.specification}
                  onChange={(e) =>
                    setNewOrder({
                      ...newOrder,
                      specification: e.target.value,
                    })
                  }
                  placeholder="规格"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  计划数量
                </label>
                <Input
                  type="number"
                  value={newOrder.plan_qty}
                  onChange={(e) =>
                    setNewOrder({
                      ...newOrder,
                      plan_qty: parseFloat(e.target.value) || 0,
                    })
                  }
                  placeholder="0"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  标准工时（小时）
                </label>
                <Input
                  type="number"
                  value={newOrder.standard_hours}
                  onChange={(e) =>
                    setNewOrder({
                      ...newOrder,
                      standard_hours: parseFloat(e.target.value) || 0,
                    })
                  }
                  placeholder="0"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  计划开始日期
                </label>
                <Input
                  type="date"
                  value={newOrder.plan_start_date}
                  onChange={(e) =>
                    setNewOrder({
                      ...newOrder,
                      plan_start_date: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  计划结束日期
                </label>
                <Input
                  type="date"
                  value={newOrder.plan_end_date}
                  onChange={(e) =>
                    setNewOrder({
                      ...newOrder,
                      plan_end_date: e.target.value,
                    })
                  }
                />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">优先级</label>
              <Select
                value={newOrder.priority}
                onValueChange={(val) =>
                  setNewOrder({ ...newOrder, priority: val })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(priorityConfigs).map(([key, config]) => (
                    <SelectItem key={key} value={key || "unknown"}>
                      {config.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">
                工作内容
              </label>
              <textarea
                className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={newOrder.work_content}
                onChange={(e) =>
                  setNewOrder({ ...newOrder, work_content: e.target.value })
                }
                placeholder="工作内容描述..."
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
