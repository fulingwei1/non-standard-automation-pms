/**
 * Create/Edit Cost Form Dialog
 */



import { CURRENCY_OPTIONS } from "./constants";

export default function CostFormDialog({
  open,
  onOpenChange,
  formData,
  setFormData,
  suppliers,
  selectedCost,
  onSave,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{selectedCost ? "编辑成本" : "新增成本"}</DialogTitle>
          <DialogDescription>
            采购部提交历史采购物料成本信息
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>物料编码</Label>
              <Input
                value={formData.material_code}
                onChange={(e) =>
                  setFormData({ ...formData, material_code: e.target.value })
                }
                placeholder="MAT-001"
              />
            </div>
            <div>
              <Label>物料名称 *</Label>
              <Input
                value={formData.material_name}
                onChange={(e) =>
                  setFormData({ ...formData, material_name: e.target.value })
                }
                placeholder="工控机"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>规格型号</Label>
              <Input
                value={formData.specification}
                onChange={(e) =>
                  setFormData({ ...formData, specification: e.target.value })
                }
                placeholder="研华IPC-610H"
              />
            </div>
            <div>
              <Label>品牌</Label>
              <Input
                value={formData.brand}
                onChange={(e) =>
                  setFormData({ ...formData, brand: e.target.value })
                }
                placeholder="研华"
              />
            </div>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div>
              <Label>单位</Label>
              <Input
                value={formData.unit}
                onChange={(e) =>
                  setFormData({ ...formData, unit: e.target.value })
                }
                placeholder="件"
              />
            </div>
            <div>
              <Label>物料类型</Label>
              <Input
                value={formData.material_type}
                onChange={(e) =>
                  setFormData({ ...formData, material_type: e.target.value })
                }
                placeholder="标准件/电气件"
              />
            </div>
            <div className="flex items-center gap-2 pt-6">
              <input
                type="checkbox"
                checked={formData.is_standard_part}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    is_standard_part: e.target.checked,
                  })
                }
                className="rounded"
              />
              <Label>标准件</Label>
            </div>
            <div className="flex items-center gap-2 pt-6">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) =>
                  setFormData({ ...formData, is_active: e.target.checked })
                }
                className="rounded"
              />
              <Label>启用匹配</Label>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label>单位成本 *</Label>
              <Input
                type="number"
                value={formData.unit_cost}
                onChange={(e) =>
                  setFormData({ ...formData, unit_cost: e.target.value })
                }
                placeholder="0.00"
                required
              />
            </div>
            <div>
              <Label>币种</Label>
              <Select
                value={formData.currency}
                onValueChange={(value) =>
                  setFormData({ ...formData, currency: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CURRENCY_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>匹配优先级</Label>
              <Input
                type="number"
                value={formData.match_priority}
                onChange={(e) =>
                  setFormData({ ...formData, match_priority: e.target.value })
                }
                placeholder="0"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>供应商</Label>
              <Select
                value={formData.supplier_id?.toString()}
                onValueChange={(value) => {
                  const supplier = (suppliers || []).find(
                    (s) => s.id.toString() === value
                  );
                  setFormData({
                    ...formData,
                    supplier_id: value,
                    supplier_name: supplier?.supplier_name || "",
                  });
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择供应商" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none__">无</SelectItem>
                  {(suppliers || []).map((s) => (
                    <SelectItem key={s.id} value={s.id.toString()}>
                      {s.supplier_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>供应商名称（手动输入）</Label>
              <Input
                value={formData.supplier_name}
                onChange={(e) =>
                  setFormData({ ...formData, supplier_name: e.target.value })
                }
                placeholder="供应商名称"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label>采购日期</Label>
              <Input
                type="date"
                value={formData.purchase_date}
                onChange={(e) =>
                  setFormData({ ...formData, purchase_date: e.target.value })
                }
              />
            </div>
            <div>
              <Label>采购订单号</Label>
              <Input
                value={formData.purchase_order_no}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    purchase_order_no: e.target.value,
                  })
                }
                placeholder="PO-20250101-001"
              />
            </div>
            <div>
              <Label>采购数量</Label>
              <Input
                type="number"
                value={formData.purchase_quantity}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    purchase_quantity: e.target.value,
                  })
                }
                placeholder="0"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>交期(天)</Label>
              <Input
                type="number"
                value={formData.lead_time_days}
                onChange={(e) =>
                  setFormData({ ...formData, lead_time_days: e.target.value })
                }
                placeholder="7"
              />
            </div>
            <div>
              <Label>匹配关键词</Label>
              <Input
                value={formData.match_keywords}
                onChange={(e) =>
                  setFormData({ ...formData, match_keywords: e.target.value })
                }
                placeholder="关键词1,关键词2（逗号分隔）"
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
              placeholder="备注信息..."
              rows={3}
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            取消
          </Button>
          <Button
            onClick={onSave}
            disabled={!formData.material_name || !formData.unit_cost}
          >
            保存
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
