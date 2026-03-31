import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { severityConfigs, typeConfigs } from "./constants";

/**
 * CreateExceptionDialog
 * Modal form for creating a new exception event.
 */
export function CreateExceptionDialog({
  open,
  onOpenChange,
  newException,
  setNewException,
  onSubmit,
  projects,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>新建异常事件</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            {/* Title */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                异常标题 *
              </label>
              <Input
                value={newException.event_title}
                onChange={(e) =>
                  setNewException({
                    ...newException,
                    event_title: e.target.value,
                  })
                }
                placeholder="请输入异常标题"
              />
            </div>

            {/* Project + Type */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">项目</label>
                <Select
                  value={newException.project_id?.toString() || ""}
                  onValueChange={(val) =>
                    setNewException({
                      ...newException,
                      project_id: val ? parseInt(val) : null,
                    })
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
              <div>
                <label className="text-sm font-medium mb-2 block">
                  异常类型
                </label>
                <Select
                  value={newException.event_type}
                  onValueChange={(val) =>
                    setNewException({ ...newException, event_type: val })
                  }
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
            </div>

            {/* Severity + Impact scope */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  严重程度
                </label>
                <Select
                  value={newException.severity}
                  onValueChange={(val) =>
                    setNewException({ ...newException, severity: val })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(severityConfigs).map(([key, config]) => (
                      <SelectItem key={key} value={key || "unknown"}>
                        {config.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  影响范围
                </label>
                <Select
                  value={newException.impact_scope}
                  onValueChange={(val) =>
                    setNewException({ ...newException, impact_scope: val })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="LOCAL">局部</SelectItem>
                    <SelectItem value="PROJECT">项目级</SelectItem>
                    <SelectItem value="SYSTEM">系统级</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                异常描述
              </label>
              <textarea
                className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={newException.event_description}
                onChange={(e) =>
                  setNewException({
                    ...newException,
                    event_description: e.target.value,
                  })
                }
                placeholder="详细描述异常情况..."
              />
            </div>

            {/* Schedule + Cost impact */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  进度影响（天）
                </label>
                <Input
                  type="number"
                  value={newException.schedule_impact}
                  onChange={(e) =>
                    setNewException({
                      ...newException,
                      schedule_impact: parseFloat(e.target.value) || 0,
                    })
                  }
                  placeholder="0"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  成本影响（元）
                </label>
                <Input
                  type="number"
                  value={newException.cost_impact}
                  onChange={(e) =>
                    setNewException({
                      ...newException,
                      cost_impact: parseFloat(e.target.value) || 0,
                    })
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
          <Button onClick={onSubmit}>创建</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
