import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui";
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
import { cn } from "../../lib/utils";
import { UNIT_TYPES } from "./unitTypeConfig";

export default function CreateDialog({
  open,
  onOpenChange,
  parentUnit,
  formData,
  setFormData,
  onFormChange,
  onSubmit,
  onCancel,
  resetForm,
}) {
  return (
    <Dialog open={open} onOpenChange={(isOpen) => { onOpenChange(isOpen); if (!isOpen) {resetForm();} }}>
      <DialogContent className="sm:max-w-[550px]">
        <DialogHeader>
          <DialogTitle>
            {parentUnit ? `在"${parentUnit.unit_name}"下新增组织` : "新增组织"}
          </DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">组织类型 *</Label>
            <Select
              value={formData.unit_type}
              onValueChange={(value) => setFormData((prev) => ({ ...prev, unit_type: value }))}
            >
              <SelectTrigger className="col-span-3">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {UNIT_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    <div className="flex items-center gap-2">
                      <type.icon className={cn("h-4 w-4", type.color)}  />
                      {type.label}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">组织编码 *</Label>
            <div className="col-span-3 space-y-1">
              <Input
                name="unit_code"
                value={formData.unit_code}
                onChange={onFormChange}
                placeholder="如：BU001, DEPT_SALES"
                className="font-mono"
              />
              <p className="text-xs text-muted-foreground">建议使用大写字母和下划线</p>
            </div>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">组织名称 *</Label>
            <Input
              name="unit_name"
              value={formData.unit_name}
              onChange={onFormChange}
              className="col-span-3"
              placeholder="如：销售一部"
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
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>取消</Button>
          <Button onClick={onSubmit}>创建</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
