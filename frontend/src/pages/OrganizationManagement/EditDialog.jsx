import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui";
import { Badge } from "../../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { getUnitTypeConfig } from "./unitTypeConfig";

export default function EditDialog({
  open,
  onOpenChange,
  formData,
  setFormData,
  onFormChange,
  onSubmit,
  onCancel,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[550px]">
        <DialogHeader>
          <DialogTitle>编辑组织</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">组织类型</Label>
            <div className="col-span-3">
              <Badge variant="outline" className={getUnitTypeConfig(formData.unit_type).color}>
                {getUnitTypeConfig(formData.unit_type).label}
              </Badge>
              <p className="text-xs text-muted-foreground mt-1">类型创建后不可修改</p>
            </div>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">组织编码</Label>
            <Input
              value={formData.unit_code}
              className="col-span-3 font-mono"
              disabled
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">组织名称 *</Label>
            <Input
              name="unit_name"
              value={formData.unit_name}
              onChange={onFormChange}
              className="col-span-3"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">排序号</Label>
            <Input
              name="sort_order"
              type="number"
              value={formData.sort_order}
              onChange={onFormChange}
              className="col-span-3"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">描述</Label>
            <Textarea
              name="description"
              value={formData.description}
              onChange={onFormChange}
              className="col-span-3"
              rows={2}
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">状态</Label>
            <Select
              value={formData.is_active ? "active" : "inactive"}
              onValueChange={(value) => setFormData((prev) => ({ ...prev, is_active: value === "active" }))}
            >
              <SelectTrigger className="col-span-3">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="active">启用</SelectItem>
                <SelectItem value="inactive">禁用</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>取消</Button>
          <Button onClick={onSubmit}>保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
