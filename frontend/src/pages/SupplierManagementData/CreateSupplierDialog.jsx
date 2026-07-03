import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
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

export default function CreateSupplierDialog({
  open,
  onOpenChange,
  newSupplier,
  onFieldChange,
  onTypeChange,
  onSubmit,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] bg-slate-900 border-slate-700">
        <DialogHeader>
          <DialogTitle className="text-slate-200">新增供应商</DialogTitle>
          <DialogDescription>
            新增供应商档案后可用于采购申请、采购订单和收货业务。
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label
              htmlFor="create-supplier-code"
              className="text-right text-slate-400"
            >
              供应商编码 *
            </Label>
            <Input
              id="create-supplier-code"
              name="supplier_code"
              value={newSupplier.supplier_code}
              onChange={onFieldChange}
              className="col-span-3 bg-slate-800 border-slate-700 text-slate-200"
              required
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="create-supplier-name" className="text-right">
              供应商名称 *
            </Label>
            <Input
              id="create-supplier-name"
              name="supplier_name"
              value={newSupplier.supplier_name}
              onChange={onFieldChange}
              className="col-span-3"
              required
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="create-supplier-type" className="text-right">
              供应商类型
            </Label>
            <Select value={newSupplier.supplier_type} onValueChange={onTypeChange}>
              <SelectTrigger className="col-span-3">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="MATERIAL">物料供应商</SelectItem>
                <SelectItem value="OUTSOURCE">外协供应商</SelectItem>
                <SelectItem value="BOTH">两者兼有</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label
              htmlFor="create-contact-person"
              className="text-right text-slate-400"
            >
              联系人
            </Label>
            <Input
              id="create-contact-person"
              name="contact_person"
              value={newSupplier.contact_person}
              onChange={onFieldChange}
              className="col-span-3 bg-slate-800 border-slate-700 text-slate-200"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label
              htmlFor="create-contact-phone"
              className="text-right text-slate-400"
            >
              联系电话
            </Label>
            <Input
              id="create-contact-phone"
              name="contact_phone"
              value={newSupplier.contact_phone}
              onChange={onFieldChange}
              className="col-span-3 bg-slate-800 border-slate-700 text-slate-200"
            />
          </div>
        </div>
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
