


export default function ConvertLeadDialog({
  open,
  onOpenChange,
  customers,
  onConvert,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>线索转商机</DialogTitle>
          <DialogDescription>选择客户后，将线索转为商机</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>选择客户 *</Label>
            <select
              id="customer-select"
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
              onChange={(e) => {
                const customerId = parseInt(e.target.value);
                if (customerId) {
                  onConvert(customerId);
                }
              }}
            >
              <option value="">请选择客户</option>
              {customers.map((customer) => (
                <option key={customer.id} value={customer.id}>
                  {customer.customer_name} ({customer.customer_code})
                </option>
              ))}
            </select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
