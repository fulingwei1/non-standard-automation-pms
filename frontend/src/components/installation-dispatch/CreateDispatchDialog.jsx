

import { Button, Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, Input, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, Textarea } from "../ui";
import {
  INSTALLATION_TYPE,
  INSTALLATION_TYPE_LABELS,
  DISPATCH_PRIORITY,
  DISPATCH_PRIORITY_LABELS,
} from "./index";

export default function CreateDispatchDialog({
  open,
  onOpenChange,
  createData,
  onDataChange,
  projects,
  machines,
  onCreate,
  loading = false,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>新建派工单</DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium">项目</label>
            <Select
              value={createData.project_id}
              onValueChange={(value) =>
                onDataChange({ ...createData, project_id: value })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="选择项目" />
              </SelectTrigger>
              <SelectContent>
                {(projects || []).map((project) => (
                  <SelectItem key={project.id} value={project.id}>
                    {project.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium">设备</label>
            <Select
              value={createData.machine_id}
              onValueChange={(value) =>
                onDataChange({ ...createData, machine_id: value })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="选择设备" />
              </SelectTrigger>
              <SelectContent>
                {(machines || []).map((machine) => (
                  <SelectItem key={machine.id} value={machine.id}>
                    {machine.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium">任务类型</label>
            <Select
              value={createData.task_type}
              onValueChange={(value) =>
                onDataChange({ ...createData, task_type: value })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="选择任务类型" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(INSTALLATION_TYPE).map(([_key, value]) => (
                  <SelectItem key={value} value={value}>
                    {INSTALLATION_TYPE_LABELS[value]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium">优先级</label>
            <Select
              value={createData.priority}
              onValueChange={(value) =>
                onDataChange({ ...createData, priority: value })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="选择优先级" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(DISPATCH_PRIORITY).map(([_key, value]) => (
                  <SelectItem key={value} value={value}>
                    {DISPATCH_PRIORITY_LABELS[value]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="col-span-2">
            <label className="text-sm font-medium">任务标题</label>
            <Input
              value={createData.task_title}
              onChange={(e) =>
                onDataChange({ ...createData, task_title: e.target.value })
              }
              placeholder="输入任务标题"
            />
          </div>
          <div className="col-span-2">
            <label className="text-sm font-medium">任务描述</label>
            <Textarea
              value={createData.task_description}
              onChange={(e) =>
                onDataChange({
                  ...createData,
                  task_description: e.target.value,
                })
              }
              placeholder="输入任务描述"
              rows={3}
            />
          </div>
          <div>
            <label className="text-sm font-medium">地点</label>
            <Input
              value={createData.location}
              onChange={(e) =>
                onDataChange({ ...createData, location: e.target.value })
              }
              placeholder="输入安装地点"
            />
          </div>
          <div>
            <label className="text-sm font-medium">计划日期</label>
            <Input
              type="date"
              value={createData.scheduled_date}
              onChange={(e) =>
                onDataChange({
                  ...createData,
                  scheduled_date: e.target.value,
                })
              }
            />
          </div>
          <div>
            <label className="text-sm font-medium">预计工时</label>
            <Input
              type="number"
              value={createData.estimated_hours}
              onChange={(e) =>
                onDataChange({
                  ...createData,
                  estimated_hours: e.target.value,
                })
              }
              placeholder="小时"
            />
          </div>
          <div>
            <label className="text-sm font-medium">客户电话</label>
            <Input
              value={createData.customer_phone}
              onChange={(e) =>
                onDataChange({ ...createData, customer_phone: e.target.value })
              }
              placeholder="输入客户电话"
            />
          </div>
          <div className="col-span-2">
            <label className="text-sm font-medium">客户地址</label>
            <Input
              value={createData.customer_address}
              onChange={(e) =>
                onDataChange({
                  ...createData,
                  customer_address: e.target.value,
                })
              }
              placeholder="输入客户地址"
            />
          </div>
          <div className="col-span-2">
            <label className="text-sm font-medium">备注</label>
            <Textarea
              value={createData.remark}
              onChange={(e) =>
                onDataChange({ ...createData, remark: e.target.value })
              }
              placeholder="输入备注信息"
              rows={2}
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
