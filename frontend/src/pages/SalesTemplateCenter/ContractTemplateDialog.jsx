import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../../components/ui/dialog";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Textarea } from "../../components/ui/textarea";
import { Label } from "../../components/ui/label";

export default function ContractTemplateDialog({
  open,
  onOpenChange,
  formData,
  setFormData,
  onSubmit,
}) {
  const update = (field) => (e) =>
    setFormData((prev) => ({ ...prev, [field]: e.target.value }));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>新建合同模板</DialogTitle>
          <DialogDescription>
            配置条款章节与审批指引，提升 G4 自检效率。
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 gap-2 items-center">
            <Label>模板编码</Label>
            <Input
              className="col-span-3"
              value={formData.template_code}
              onChange={update("template_code")}
            />
          </div>
          <div className="grid grid-cols-4 gap-2 items-center">
            <Label>模板名称</Label>
            <Input
              className="col-span-3"
              value={formData.template_name}
              onChange={update("template_name")}
            />
          </div>
          <div className="grid grid-cols-4 gap-2 items-center">
            <Label>合同类型</Label>
            <Input
              className="col-span-3"
              value={formData.contract_type}
              onChange={update("contract_type")}
            />
          </div>
          <div className="grid grid-cols-4 gap-2 items-center">
            <Label>版本号</Label>
            <Input
              className="col-span-3"
              value={formData.version_no}
              onChange={update("version_no")}
            />
          </div>
          <div className="grid grid-cols-4 gap-2 items-start">
            <Label>条款结构 JSON</Label>
            <Textarea
              className="col-span-3 min-h-[120px]"
              value={formData.clause_sections}
              onChange={update("clause_sections")}
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
