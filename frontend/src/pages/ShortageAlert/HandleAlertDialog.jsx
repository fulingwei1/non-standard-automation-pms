import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
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

export default function HandleAlertDialog({
  open,
  onOpenChange,
  selectedAlert,
  handleData,
  setHandleData,
  onResolve,
}) {
  const updateField = (field) => (value) =>
    setHandleData((prev) => ({ ...prev, [field]: value }));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-slate-900 border-slate-700">
        <DialogHeader>
          <DialogTitle className="text-slate-200">处理缺料预警</DialogTitle>
        </DialogHeader>
        <DialogBody>
          {selectedAlert && (
            <div className="space-y-4">
              <div>
                <div className="text-sm text-slate-400 mb-1">物料</div>
                <div className="font-medium text-slate-200">
                  {selectedAlert.material_name}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-400 mb-1">缺料数量</div>
                <div className="font-medium text-red-400">
                  {selectedAlert.shortage_qty || 0}
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block text-slate-400">
                  处理状态
                </label>
                <Select
                  value={handleData.status}
                  onValueChange={updateField("status")}
                >
                  <SelectTrigger className="bg-slate-800 border-slate-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PROCESSING">处理中</SelectItem>
                    <SelectItem value="RESOLVED">已解决</SelectItem>
                    <SelectItem value="CLOSED">已关闭</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block text-slate-400">
                  解决方案
                </label>
                <textarea
                  className="w-full min-h-[100px] p-3 border border-slate-700 rounded-lg bg-slate-800 text-slate-200 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={handleData.solution}
                  onChange={(e) => updateField("solution")(e.target.value)}
                  placeholder="填写解决方案..."
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block text-slate-400">
                  备注
                </label>
                <Input
                  value={handleData.remark}
                  onChange={(e) => updateField("remark")(e.target.value)}
                  placeholder="备注信息"
                  className="bg-slate-800 border-slate-700 text-slate-200"
                />
              </div>
            </div>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onResolve}>保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
