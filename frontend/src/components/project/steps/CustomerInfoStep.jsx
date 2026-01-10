import React from 'react'
import { Button, Input } from '../../ui'
import { Building2 } from 'lucide-react'

/**
 * 客户信息步骤组件
 */
export const CustomerInfoStep = ({
  formData,
  setFormData,
  customerSearch,
  setCustomerSearch,
  filteredCustomers,
  selectedCustomer,
  setSelectedCustomer,
  onCustomerSelect,
}) => {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-300">
          客户 <span className="text-red-400">*</span>
        </label>
        <div className="space-y-2">
          <Input
            value={customerSearch}
            onChange={(e) => setCustomerSearch(e.target.value)}
            placeholder="搜索客户名称或编码"
            icon={Building2}
          />
          {customerSearch && (
            <div className="max-h-48 overflow-y-auto border border-white/10 rounded-lg bg-slate-900/50">
              {filteredCustomers.length > 0 ? (
                filteredCustomers.map((customer) => (
                  <div
                    key={customer.id}
                    className="p-3 hover:bg-white/5 cursor-pointer border-b border-white/5 last:border-0"
                    onClick={() => onCustomerSelect(customer.id)}
                  >
                    <div className="font-medium text-white">
                      {customer.customer_name}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      {customer.customer_code}
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-3 text-sm text-slate-400 text-center">
                  未找到匹配的客户
                </div>
              )}
            </div>
          )}
          {selectedCustomer && (
            <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-white">
                    {selectedCustomer.customer_name}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    {selectedCustomer.customer_code}
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setSelectedCustomer(null)
                    setFormData((prev) => ({
                      ...prev,
                      customer_id: '',
                      customer_name: '',
                      customer_contact: '',
                      customer_phone: '',
                    }))
                  }}
                >
                  清除
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">联系人</label>
          <Input
            value={formData.customer_contact}
            onChange={(e) =>
              setFormData({ ...formData, customer_contact: e.target.value })
            }
            placeholder="客户联系人"
            disabled={!selectedCustomer}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">联系电话</label>
          <Input
            value={formData.customer_phone}
            onChange={(e) =>
              setFormData({ ...formData, customer_phone: e.target.value })
            }
            placeholder="客户联系电话"
            disabled={!selectedCustomer}
          />
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-300">合同编号</label>
        <Input
          value={formData.contract_no}
          onChange={(e) =>
            setFormData({ ...formData, contract_no: e.target.value })
          }
          placeholder="合同编号（可选）"
        />
      </div>
    </div>
  )
}
