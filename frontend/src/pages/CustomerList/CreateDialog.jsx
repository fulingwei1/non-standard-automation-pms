import {
  Button,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../../components/ui"

export function CreateDialog({
  open,
  onOpenChange,
  createForm,
  setCreateForm,
  onSubmit,
  creating,
  onReset,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>新建客户</DialogTitle>
          <DialogDescription>
            创建新的客户档案，填写基本信息
          </DialogDescription>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-4 py-4">
          <div className="space-y-2">
            <label className="text-sm text-slate-400">公司全称 *</label>
            <Input
              placeholder="请输入公司全称"
              value={createForm.customer_name}
              onChange={(e) =>
                setCreateForm((prev) => ({ ...prev, customer_name: e.target.value }))
              }
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">公司简称</label>
            <Input
              placeholder="请输入公司简称"
              value={createForm.short_name}
              onChange={(e) =>
                setCreateForm((prev) => ({ ...prev, short_name: e.target.value }))
              }
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">客户等级</label>
            <select
              value={createForm.customer_level}
              onChange={(e) =>
                setCreateForm((prev) => ({ ...prev, customer_level: e.target.value }))
              }
              className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white"
            >
              <option value="B">B级客户</option>
              <option value="A">A级客户</option>
              <option value="C">C级客户</option>
              <option value="D">D级客户</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">所属行业</label>
            <select
              value={createForm.industry}
              onChange={(e) =>
                setCreateForm((prev) => ({ ...prev, industry: e.target.value }))
              }
              className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white"
            >
              <option value="">请选择行业</option>
              <option value="新能源电池">新能源电池</option>
              <option value="消费电子">消费电子</option>
              <option value="汽车零部件">汽车零部件</option>
              <option value="储能系统">储能系统</option>
              <option value="智能制造">智能制造</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">联系人</label>
            <Input
              placeholder="请输入联系人姓名"
              value={createForm.contact_name}
              onChange={(e) =>
                setCreateForm((prev) => ({ ...prev, contact_name: e.target.value }))
              }
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">联系电话</label>
            <Input
              placeholder="请输入联系电话"
              value={createForm.phone}
              onChange={(e) =>
                setCreateForm((prev) => ({ ...prev, phone: e.target.value }))
              }
            />
          </div>
          <div className="col-span-2 space-y-2">
            <label className="text-sm text-slate-400">公司地址</label>
            <Input
              placeholder="请输入公司地址"
              value={createForm.address}
              onChange={(e) =>
                setCreateForm((prev) => ({ ...prev, address: e.target.value }))
              }
            />
          </div>
          <div className="col-span-2 space-y-2">
            <label className="text-sm text-slate-400">备注</label>
            <textarea
              placeholder="请输入备注信息"
              value={createForm.remark}
              onChange={(e) =>
                setCreateForm((prev) => ({ ...prev, remark: e.target.value }))
              }
              className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white resize-none h-20"
            />
          </div>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => {
              onOpenChange(false);
              onReset();
            }}
            disabled={creating}
          >
            取消
          </Button>
          <Button onClick={onSubmit} disabled={creating}>
            {creating ? "创建中..." : "创建客户"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
