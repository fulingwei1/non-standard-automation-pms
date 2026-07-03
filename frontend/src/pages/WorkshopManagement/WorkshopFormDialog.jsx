import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../../components/ui/dialog";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { typeConfigs } from "./constants";

/**
 * Shared form dialog for creating and editing workshops.
 * Controlled by `mode` prop: "create" | "edit"
 */
export function WorkshopFormDialog({
  mode,
  open,
  onOpenChange,
  workshopForm,
  setWorkshopForm,
  managers,
  onSubmit,
}) {
  const isEdit = mode === "edit";

  const handleField = (field, value) => {
    setWorkshopForm((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{isEdit ? "编辑车间" : "新建车间"}</DialogTitle>
          <DialogDescription>
            {isEdit ? "修改车间基础信息和启用状态。" : "录入车间编码、名称、类型和产能信息。"}
          </DialogDescription>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  车间编码 *
                </label>
                <Input
                  value={workshopForm.workshop_code}
                  onChange={(e) => handleField("workshop_code", e.target.value)}
                  placeholder="请输入车间编码"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  车间名称 *
                </label>
                <Input
                  value={workshopForm.workshop_name}
                  onChange={(e) => handleField("workshop_name", e.target.value)}
                  placeholder="请输入车间名称"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  车间类型
                </label>
                <Select
                  value={workshopForm.workshop_type}
                  onValueChange={(val) => handleField("workshop_type", val)}
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
                  车间主管
                </label>
                <Select
                  value={workshopForm.manager_id?.toString() || ""}
                  onValueChange={(val) =>
                    handleField("manager_id", val ? parseInt(val) : null)
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择主管" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">无</SelectItem>
                    {(managers || []).map((mgr) => (
                      <SelectItem key={mgr.id} value={mgr.id.toString()}>
                        {mgr.real_name || mgr.username}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">位置</label>
                <Input
                  value={workshopForm.location}
                  onChange={(e) => handleField("location", e.target.value)}
                  placeholder="车间位置"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  产能（小时）
                </label>
                <Input
                  type="number"
                  value={workshopForm.capacity_hours}
                  onChange={(e) =>
                    handleField(
                      "capacity_hours",
                      parseFloat(e.target.value) || 0
                    )
                  }
                  placeholder="0"
                />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">描述</label>
              <textarea
                className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={workshopForm.description}
                onChange={(e) => handleField("description", e.target.value)}
                placeholder="车间描述..."
              />
            </div>
            {isEdit && (
              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={workshopForm.is_active}
                    onChange={(e) =>
                      handleField("is_active", e.target.checked)
                    }
                  />
                  <span className="text-sm">启用</span>
                </label>
              </div>
            )}
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit}>{isEdit ? "保存" : "创建"}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
