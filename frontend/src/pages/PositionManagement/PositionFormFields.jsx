import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { POSITION_CATEGORIES } from "./categoryConstants";

export default function PositionFormFields({
  formData,
  handleFormChange,
  setFormData,
  orgUnits,
  isEdit = false,
}) {
  return (
    <div className="grid gap-4 py-4">
      <div className="grid grid-cols-4 items-center gap-4">
        <Label className="text-right">岗位编码{isEdit ? "" : " *"}</Label>
        {isEdit ? (
          <Input value={formData.position_code} className="col-span-3 font-mono" disabled />
        ) : (
          <div className="col-span-3 space-y-1">
            <Input
              name="position_code"
              value={formData.position_code}
              onChange={handleFormChange}
              placeholder="如：PM_SENIOR, ENGINEER_L3"
              className="font-mono"
            />
            <p className="text-xs text-muted-foreground">建议使用大写字母和下划线</p>
          </div>
        )}
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label className="text-right">岗位名称 *</Label>
        <Input
          name="position_name"
          value={formData.position_name}
          onChange={handleFormChange}
          className="col-span-3"
          placeholder={isEdit ? undefined : "如：高级项目经理"}
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label className="text-right">岗位类别{isEdit ? "" : " *"}</Label>
        <Select
          value={formData.position_category}
          onValueChange={(value) => setFormData((prev) => ({ ...prev, position_category: value }))}
        >
          <SelectTrigger className="col-span-3">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {POSITION_CATEGORIES.map((cat) => (
              <SelectItem key={cat.value} value={cat.value}>
                {cat.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label className="text-right">所属组织</Label>
        <Select
          value={formData.org_unit_id?.toString() || "none"}
          onValueChange={(value) => setFormData((prev) => ({ ...prev, org_unit_id: value === "none" ? null : parseInt(value) }))}
        >
          <SelectTrigger className="col-span-3">
            <SelectValue placeholder={isEdit ? "选择所属组织" : "选择所属组织（可选）"} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">不限制组织</SelectItem>
            {(orgUnits || []).map((org) => (
              <SelectItem key={org.id} value={org.id.toString()}>
                {org.unit_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label className="text-right">描述</Label>
        <Textarea
          name="description"
          value={formData.description}
          onChange={handleFormChange}
          className="col-span-3"
          rows={2}
          placeholder={isEdit ? undefined : "岗位职责描述..."}
        />
      </div>
      {isEdit ? (
        <>
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
        </>
      ) : (
        <div className="grid grid-cols-4 items-center gap-4">
          <Label className="text-right">排序号</Label>
          <Input
            name="sort_order"
            type="number"
            value={formData.sort_order}
            onChange={handleFormChange}
            className="col-span-3"
          />
        </div>
      )}
    </div>
  );
}
