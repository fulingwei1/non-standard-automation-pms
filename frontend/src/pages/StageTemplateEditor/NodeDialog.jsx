import { Plus, Edit3 } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Badge } from "../../components/ui/badge";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";

export default function NodeDialog({
  open,
  onOpenChange,
  mode,
  formData,
  setFormData,
  selectedStageForNode,
  onSave,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {mode === "create" ? (
              <>
                <Plus className="h-5 w-5 text-violet-400" />
                添加节点
              </>
            ) : (
              <>
                <Edit3 className="h-5 w-5 text-violet-400" />
                编辑节点
              </>
            )}
            <Badge variant="outline" className="bg-violet-500/20 text-violet-400 border-violet-500/30">
              {selectedStageForNode?.stage_code}
            </Badge>
          </DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>节点编码 *</Label>
              <Input
                placeholder="如 S1_N1"
                value={formData.node_code}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, node_code: e.target.value.toUpperCase() }))
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
            <Label>节点名称 *</Label>
            <Input
              placeholder="如 需求调研"
              value={formData.node_name}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, node_name: e.target.value }))
              }
              className="bg-white/5 border-white/10"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>节点类型</Label>
              <Select
                value={formData.node_type}
                onValueChange={(v) => setFormData((prev) => ({ ...prev, node_type: v }))}
              >
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="TASK">任务节点</SelectItem>
                  <SelectItem value="APPROVAL">审批节点</SelectItem>
                  <SelectItem value="DELIVERABLE">交付物节点</SelectItem>
                </SelectContent>
              </Select>
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
          </div>
          <div className="space-y-2">
            <Label>完成方式</Label>
            <Select
              value={formData.completion_method}
              onValueChange={(v) => setFormData((prev) => ({ ...prev, completion_method: v }))}
            >
              <SelectTrigger className="bg-white/5 border-white/10">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="MANUAL">手动完成</SelectItem>
                <SelectItem value="APPROVAL">需要审批</SelectItem>
                <SelectItem value="UPLOAD">上传附件</SelectItem>
                <SelectItem value="AUTO">自动完成</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>节点描述</Label>
            <Textarea
              placeholder="描述该节点的工作内容..."
              value={formData.description}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, description: e.target.value }))
              }
              className="bg-white/5 border-white/10 min-h-[60px]"
            />
          </div>
          {formData.completion_method === "AUTO" && (
            <div className="space-y-2">
              <Label>自动完成条件 (JSON)</Label>
              <Textarea
                placeholder='{"field": "value"}'
                value={formData.auto_condition}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, auto_condition: e.target.value }))
                }
                className="bg-white/5 border-white/10 min-h-[60px] font-mono text-sm"
              />
            </div>
          )}
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <Switch
                id="node_required"
                checked={formData.is_required}
                onCheckedChange={(v) => setFormData((prev) => ({ ...prev, is_required: v }))}
              />
              <Label htmlFor="node_required" className="cursor-pointer">
                必需节点
              </Label>
            </div>
            <div className="flex items-center gap-2">
              <Switch
                id="node_attachments"
                checked={formData.required_attachments}
                onCheckedChange={(v) =>
                  setFormData((prev) => ({ ...prev, required_attachments: v }))
                }
              />
              <Label htmlFor="node_attachments" className="cursor-pointer">
                需要上传附件
              </Label>
            </div>
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
