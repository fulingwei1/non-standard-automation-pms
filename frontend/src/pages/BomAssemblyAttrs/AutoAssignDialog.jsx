/**
 * Auto Assign Dialog - 自动分配装配属性对话框
 */
import { AlertTriangle, Wand2 } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Label } from "../../components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../../components/ui/dialog";
import { Switch } from "../../components/ui/switch";

export function AutoAssignDialog({
  open,
  onOpenChange,
  overwrite,
  setOverwrite,
  loading,
  onAutoAssign,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>自动分配装配属性</DialogTitle>
          <DialogDescription>
            根据物料分类自动分配装配阶段和阻塞性设置
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>覆盖已有配置</Label>
              <p className="text-sm text-slate-500">
                是否覆盖已经配置过的物料
              </p>
            </div>
            <Switch checked={overwrite} onCheckedChange={setOverwrite} />
          </div>
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500 mt-0.5" />
              <div className="text-sm text-amber-700">
                <p className="font-medium">提示</p>
                <p>
                  自动分配会根据物料分类映射配置来设置装配阶段。请确保已配置好物料分类映射。
                </p>
              </div>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onAutoAssign} disabled={loading}>
            <Wand2 className="w-4 h-4 mr-2" />
            开始分配
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
