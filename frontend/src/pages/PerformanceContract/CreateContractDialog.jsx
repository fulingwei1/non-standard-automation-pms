import { Save } from "lucide-react";
import {
  Button,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Label,
  Textarea,
} from "@/components/ui";
import { CONTRACT_TYPE_OPTIONS } from "./constants";

export default function CreateContractDialog({
  open,
  onOpenChange,
  createForm,
  setCreateForm,
  onCreateContract,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-slate-900 border-slate-700 max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-white">创建绩效合约</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-slate-300">合约类型</Label>
              <Select
                value={createForm.contract_type}
                onValueChange={(value) => setCreateForm({ ...createForm, contract_type: value })}
              >
                <SelectTrigger className="bg-slate-800 border-slate-700 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  {CONTRACT_TYPE_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value} className="text-white">
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-slate-300">年度</Label>
              <Input
                type="number"
                value={createForm.year}
                onChange={(e) => setCreateForm({ ...createForm, year: parseInt(e.target.value) })}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-slate-300">签约人姓名</Label>
              <Input
                value={createForm.signer_name}
                onChange={(e) => setCreateForm({ ...createForm, signer_name: e.target.value })}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
            <div>
              <Label className="text-slate-300">签约人职位</Label>
              <Input
                value={createForm.signer_title}
                onChange={(e) => setCreateForm({ ...createForm, signer_title: e.target.value })}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-slate-300">对方/上级姓名</Label>
              <Input
                value={createForm.counterpart_name}
                onChange={(e) => setCreateForm({ ...createForm, counterpart_name: e.target.value })}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
            <div>
              <Label className="text-slate-300">对方/上级职位</Label>
              <Input
                value={createForm.counterpart_title}
                onChange={(e) => setCreateForm({ ...createForm, counterpart_title: e.target.value })}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
          </div>
          <div>
            <Label className="text-slate-300">部门名称</Label>
            <Input
              value={createForm.department_name}
              onChange={(e) => setCreateForm({ ...createForm, department_name: e.target.value })}
              className="bg-slate-800 border-slate-700 text-white"
            />
          </div>
          <div>
            <Label className="text-slate-300">备注</Label>
            <Textarea
              value={createForm.remarks}
              onChange={(e) => setCreateForm({ ...createForm, remarks: e.target.value })}
              className="bg-slate-800 border-slate-700 text-white"
              rows={3}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} className="border-slate-700 text-slate-300">
            取消
          </Button>
          <Button onClick={onCreateContract} className="bg-blue-600 hover:bg-blue-700">
            <Save size={16} className="mr-2" />
            创建
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
