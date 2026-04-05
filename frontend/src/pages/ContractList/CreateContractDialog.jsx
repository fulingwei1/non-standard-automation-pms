import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Button,
  Input,
} from "../../components/ui";

export default function CreateContractDialog({ open, onOpenChange }) {
  const handleClose = () => onOpenChange(false);
  const handleCreate = () => onOpenChange(false);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>新建合同</DialogTitle>
          <DialogDescription>创建新的销售合同</DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-4 py-4">
          <div className="col-span-2 space-y-2">
            <label className="text-sm text-slate-400">合同名称 *</label>
            <Input placeholder="请输入合同名称" />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">关联报价单</label>
            <select className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white">
              <option value="">请选择报价单</option>
              <option value="QT2026010001">
                QT2026010001 - BMS老化测试设备报价
              </option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">合同金额</label>
            <Input type="number" placeholder="请输入合同金额" />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">交付日期</label>
            <Input type="date" />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">质保期(月)</label>
            <Input type="number" defaultValue={12} />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            取消
          </Button>
          <Button onClick={handleCreate}>创建合同</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
