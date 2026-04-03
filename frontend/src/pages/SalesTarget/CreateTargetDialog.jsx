import {
  Button,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Label,
} from "../../components/ui";
import { targetScopeOptions, targetTypeOptions, targetPeriodOptions } from "./constants";

export default function CreateTargetDialog({
  open,
  onOpenChange,
  formData,
  setFormData,
  teamMembers,
  onCreate,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>创建销售目标</DialogTitle>
          <DialogDescription>设置个人、团队或部门销售目标</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>目标范围</Label>
              <Select
                value={formData.target_scope}
                onValueChange={(value) =>
                  setFormData((prev) => ({ ...prev, target_scope: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(targetScopeOptions || []).map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {formData.target_scope === "PERSONAL" && (
              <div>
                <Label>负责人</Label>
                <Select
                  value={formData.user_id?.toString() || ""}
                  onValueChange={(value) =>
                    setFormData((prev) => ({
                      ...prev,
                      user_id: parseInt(value),
                    }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择负责人" />
                  </SelectTrigger>
                  <SelectContent>
                    {(teamMembers || []).map((member) => (
                      <SelectItem
                        key={member.user_id}
                        value={member.user_id.toString()}
                      >
                        {member.user_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            <div>
              <Label>目标类型</Label>
              <Select
                value={formData.target_type}
                onValueChange={(value) =>
                  setFormData((prev) => ({ ...prev, target_type: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(targetTypeOptions || []).map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>目标周期</Label>
              <Select
                value={formData.target_period}
                onValueChange={(value) =>
                  setFormData((prev) => ({ ...prev, target_period: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(targetPeriodOptions || []).map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>周期值</Label>
              <Input
                value={formData.period_value}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    period_value: e.target.value,
                  }))
                }
                placeholder="如: 2025-01, 2025-Q1, 2025"
              />
            </div>
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
                placeholder="输入目标值"
              />
            </div>
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
              placeholder="目标描述（可选）"
            />
          </div>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            取消
          </Button>
          <Button onClick={onCreate}>创建</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
