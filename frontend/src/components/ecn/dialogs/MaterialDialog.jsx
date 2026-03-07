/**
 * MaterialDialog Component
 * 受影响物料对话框
 */
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../../ui/dialog";
import { Button } from "../../ui/button";
import { Input } from "../../ui/input";
import { Textarea } from "../../ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../ui/select";

export default function MaterialDialog({
  open,
  onOpenChange,
  form,
  setForm,
  onSubmit,
  editingMaterial,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {editingMaterial ? "编辑受影响物料" : "添加受影响物料"}
          </DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                物料编码 *
              </label>
              <Input
                value={form.material_code}
                onChange={(e) =>
                  setForm({ ...form, material_code: e.target.value })
                }
                placeholder="请输入物料编码"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">
                物料名称 *
              </label>
              <Input
                value={form.material_name}
                onChange={(e) =>
                  setForm({ ...form, material_name: e.target.value })
                }
                placeholder="请输入物料名称"
              />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">变更类型 *</label>
            <Select
              value={form.change_type}
              onValueChange={(value) =>
                setForm({ ...form, change_type: value })
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ADD">新增</SelectItem>
                <SelectItem value="DELETE">删除</SelectItem>
                <SelectItem value="UPDATE">修改</SelectItem>
                <SelectItem value="REPLACE">替换</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">原数量</label>
              <Input
                type="number"
                value={form.old_quantity}
                onChange={(e) =>
                  setForm({ ...form, old_quantity: e.target.value })
                }
                placeholder="变更前的数量"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">新数量</label>
              <Input
                type="number"
                value={form.new_quantity}
                onChange={(e) =>
                  setForm({ ...form, new_quantity: e.target.value })
                }
                placeholder="变更后的数量"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">原规格</label>
              <Input
                value={form.old_specification}
                onChange={(e) =>
                  setForm({ ...form, old_specification: e.target.value })
                }
                placeholder="变更前的规格"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">新规格</label>
              <Input
                value={form.new_specification}
                onChange={(e) =>
                  setForm({ ...form, new_specification: e.target.value })
                }
                placeholder="变更后的规格"
              />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">成本影响</label>
            <Input
              type="number"
              step="0.01"
              value={form.cost_impact}
              onChange={(e) =>
                setForm({
                  ...form,
                  cost_impact: parseFloat(e.target.value) || 0,
                })
              }
              placeholder="成本变化金额（正数表示增加，负数表示减少）"
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">备注</label>
            <Textarea
              value={form.remark}
              onChange={(e) => setForm({ ...form, remark: e.target.value })}
              placeholder="请输入备注"
            />
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit}>保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
