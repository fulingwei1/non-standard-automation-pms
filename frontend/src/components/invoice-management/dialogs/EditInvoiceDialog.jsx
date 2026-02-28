import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Button,
  Label,
  Input,
  Textarea
} from "../../ui";

const EditInvoiceDialog = ({
  open,
  onOpenChange,
  formData,
  setFormData,
  contracts,
  onConfirm
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>编辑发票</DialogTitle>
          <DialogDescription>更新发票信息</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>合同 *</Label>
              <select
                value={formData.contract_id}
                onChange={(e) =>
                  setFormData({ ...formData, contract_id: e.target.value })
                }
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
              >
                <option value="">请选择合同</option>
                {(contracts || []).map((contract) => (
                  <option key={contract.id} value={contract.id}>
                    {contract.contract_code} - {contract.customer_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>发票类型 *</Label>
              <select
                value={formData.invoice_type}
                onChange={(e) =>
                  setFormData({ ...formData, invoice_type: e.target.value })
                }
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
              >
                <option value="SPECIAL">专票</option>
                <option value="NORMAL">普票</option>
              </select>
            </div>
            <div>
              <Label>金额 *</Label>
              <Input
                type="number"
                value={formData.amount}
                onChange={(e) =>
                  setFormData({ ...formData, amount: e.target.value })
                }
                placeholder="请输入金额"
              />
            </div>
            <div>
              <Label>税率 (%)</Label>
              <Input
                type="number"
                value={formData.tax_rate}
                onChange={(e) =>
                  setFormData({ ...formData, tax_rate: e.target.value })
                }
                placeholder="13"
              />
            </div>
            <div>
              <Label>开票日期</Label>
              <Input
                type="date"
                value={formData.issue_date}
                onChange={(e) =>
                  setFormData({ ...formData, issue_date: e.target.value })
                }
              />
            </div>
            <div>
              <Label>到期日期</Label>
              <Input
                type="date"
                value={formData.due_date}
                onChange={(e) =>
                  setFormData({ ...formData, due_date: e.target.value })
                }
              />
            </div>
          </div>
          <div>
            <Label>备注</Label>
            <Textarea
              value={formData.remark}
              onChange={(e) =>
                setFormData({ ...formData, remark: e.target.value })
              }
              placeholder="请输入备注"
              rows={3}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onConfirm}>保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default EditInvoiceDialog;
