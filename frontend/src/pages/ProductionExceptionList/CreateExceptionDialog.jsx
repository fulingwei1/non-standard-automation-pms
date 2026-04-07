/**
 * CreateExceptionDialog — modal form for reporting a new production exception.
 */




import { typeConfigs, levelConfigs } from "./constants";

export function CreateExceptionDialog({
  open,
  onOpenChange,
  projects,
  newException,
  setNewException,
  onSubmit,
}) {
  const update = (patch) => setNewException((prev) => ({ ...prev, ...patch }));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>上报生产异常</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            {/* Title */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                异常标题 *
              </label>
              <Input
                value={newException.title}
                onChange={(e) => update({ title: e.target.value })}
                placeholder="请输入异常标题"
              />
            </div>

            {/* Type + Level */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  异常类型
                </label>
                <Select
                  value={newException.exception_type}
                  onValueChange={(val) => update({ exception_type: val })}
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
                <label className="text-sm font-medium mb-2 block">
                  异常级别
                </label>
                <Select
                  value={newException.exception_level}
                  onValueChange={(val) => update({ exception_level: val })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(levelConfigs).map(([key, config]) => (
                      <SelectItem key={key} value={key || "unknown"}>
                        {config.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Project */}
            <div>
              <label className="text-sm font-medium mb-2 block">项目</label>
              <Select
                value={newException.project_id?.toString() || ""}
                onValueChange={(val) =>
                  update({ project_id: val ? parseInt(val) : null })
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

            {/* Description */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                异常描述
              </label>
              <textarea
                className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={newException.description}
                onChange={(e) => update({ description: e.target.value })}
                placeholder="详细描述异常情况..."
              />
            </div>

            {/* Impact hours + cost */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  影响工时（小时）
                </label>
                <Input
                  type="number"
                  value={newException.impact_hours}
                  onChange={(e) =>
                    update({ impact_hours: parseFloat(e.target.value) || 0 })
                  }
                  placeholder="0"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  影响成本（元）
                </label>
                <Input
                  type="number"
                  value={newException.impact_cost}
                  onChange={(e) =>
                    update({ impact_cost: parseFloat(e.target.value) || 0 })
                  }
                  placeholder="0"
                />
              </div>
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit}>上报</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
