


export function CreateQuotationDialog({ open, onOpenChange }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>新建报价</DialogTitle>
          <DialogDescription>创建新的销售报价单</DialogDescription>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-4 py-4">
          <div className="col-span-2 space-y-2">
            <label className="text-sm text-slate-400">报价名称 *</label>
            <Input placeholder="请输入报价名称" />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">关联商机</label>
            <select className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white">
              <option value="">请选择商机</option>
              <option value="OPP001">BMS老化测试设备 - 深圳新能源</option>
              <option value="OPP003">ICT在线测试设备 - 惠州储能</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">有效期</label>
            <Input type="date" />
          </div>
          <div className="col-span-2 space-y-2">
            <label className="text-sm text-slate-400">报价明细</label>
            <div className="border border-white/10 rounded-lg p-4 bg-surface-50">
              <p className="text-sm text-slate-400 text-center">
                保存基本信息后添加报价明细
              </p>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={() => onOpenChange(false)}>创建报价</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
