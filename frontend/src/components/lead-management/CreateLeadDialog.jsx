import React from "react";
import {
  Button,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Label,
  Textarea,
} from "../../components/ui";
import { sourceOptions } from "./leadManagementConstants";

export default function CreateLeadDialog({
  open,
  onOpenChange,
  formData,
  setFormData,
  statusConfig,
  onCreate,
  customers = [],
  selectedCustomerId = "",
  onSelectCustomer,
  onCustomerNameChange,
  similarCustomers = [],
  hasExactCustomerMatch = false,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>新建线索</DialogTitle>
          <DialogDescription>创建新的销售线索</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>客户名称 *</Label>
              <select
                value={selectedCustomerId}
                onChange={(e) => {
                  const customer = customers.find(
                    (item) => String(item.id) === e.target.value
                  );
                  if (customer) {
                    onSelectCustomer?.(customer);
                  } else {
                    onSelectCustomer?.(null);
                  }
                }}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
              >
                <option value="">选择已有客户</option>
                {customers.map((customer) => (
                  <option key={customer.id} value={customer.id}>
                    {customer.customer_name}
                  </option>
                ))}
              </select>
              <Input
                value={formData.customer_name}
                onChange={(e) =>
                  onCustomerNameChange?.(e.target.value)
                }
                placeholder="或输入新客户名称"
              />
              {similarCustomers.length > 0 && !hasExactCustomerMatch && (
                <div className="mt-2 text-xs text-slate-400">
                  相似客户：
                  <div className="flex flex-wrap gap-2 mt-2">
                    {similarCustomers.map((customer) => (
                      <button
                        key={customer.id}
                        type="button"
                        onClick={() => onSelectCustomer?.(customer)}
                        className="px-2 py-1 rounded border border-slate-700 text-slate-200 hover:border-blue-500"
                      >
                        {customer.customer_name}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div>
              <Label>来源</Label>
              <select
                value={formData.source}
                onChange={(e) =>
                  setFormData({ ...formData, source: e.target.value })
                }
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
              >
                <option value="">请选择来源</option>
                {sourceOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>行业</Label>
              <Input
                value={formData.industry}
                onChange={(e) =>
                  setFormData({ ...formData, industry: e.target.value })
                }
                placeholder="请输入行业"
              />
            </div>
            <div>
              <Label>联系人</Label>
              <Input
                value={formData.contact_name}
                onChange={(e) =>
                  setFormData({ ...formData, contact_name: e.target.value })
                }
                placeholder="请输入联系人"
              />
            </div>
            <div>
              <Label>联系电话</Label>
              <Input
                value={formData.contact_phone}
                onChange={(e) =>
                  setFormData({ ...formData, contact_phone: e.target.value })
                }
                placeholder="请输入联系电话"
              />
            </div>
            <div>
              <Label>状态</Label>
              <select
                value={formData.status}
                onChange={(e) =>
                  setFormData({ ...formData, status: e.target.value })
                }
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
              >
                {["NEW", "CONTACTED", "QUALIFIED", "LOST", "CONVERTED"].map(
                  (key) => (
                    <option key={key} value={key}>
                      {statusConfig[key]?.label || key}
                    </option>
                  )
                )}
              </select>
            </div>
          </div>
          <div>
            <Label>需求摘要</Label>
            <Textarea
              value={formData.demand_summary}
              onChange={(e) =>
                setFormData({ ...formData, demand_summary: e.target.value })
              }
              placeholder="请输入需求摘要"
              rows={4}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onCreate}>创建</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
