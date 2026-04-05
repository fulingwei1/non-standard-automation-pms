import { Plus, Edit3 } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui/textarea";
import { Switch } from "../../components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody,
} from "../../components/ui/dialog";

export default function StageDialog({
  open,
  onOpenChange,
  mode,
  formData,
  setFormData,
  onSave,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {mode === "create" ? (
              <>
                <Plus className="h-5 w-5 text-violet-400" />
                添加阶段
              </>
            ) : (
              <>
                <Edit3 className="h-5 w-5 text-violet-400" />
                编辑阶段
              </>
            )}
          </DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>阶段编码 *</Label>
              <Input
                placeholder="如 S1"
                value={formData.stage_code}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, stage_code: e.target.value.toUpperCase() }))
                }
                className="bg-white/5 border-white/10"
              />
            </div>
            <div className="space-y-2">
              <Label>排序顺序</Label>
              <Input
                type="number"
                value={formData.sequence}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, sequence: parseInt(e.target.value) || 1 }))
                }
                className="bg-white/5 border-white/10"
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label>阶段名称 *</Label>
            <Input
              placeholder="如 需求进入"
              value={formData.stage_name}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, stage_name: e.target.value }))
              }
              className="bg-white/5 border-white/10"
            />
          </div>
          <div className="space-y-2">
            <Label>预估天数</Label>
            <Input
              type="number"
              value={formData.estimated_days}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, estimated_days: parseInt(e.target.value) || 1 }))
              }
              className="bg-white/5 border-white/10"
            />
          </div>
          <div className="space-y-2">
            <Label>阶段描述</Label>
            <Textarea
              placeholder="描述该阶段的主要工作内容..."
              value={formData.description}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, description: e.target.value }))
              }
              className="bg-white/5 border-white/10 min-h-[80px]"
            />
          </div>
          <div className="flex items-center gap-2">
            <Switch
              id="stage_required"
              checked={formData.is_required}
              onCheckedChange={(v) => setFormData((prev) => ({ ...prev, is_required: v }))}
            />
            <Label htmlFor="stage_required" className="cursor-pointer">
              必需阶段
            </Label>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSave}>
            {mode === "create" ? "添加" : "保存"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
